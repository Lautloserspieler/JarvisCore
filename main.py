#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
J.A.R.V.I.S. - Deutscher KI-Sprachassistent
Hauptmodul faer den Start der Anwendung
"""

import sys
import os
import threading
import time
import webbrowser
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from concurrent.futures import Future
from typing import Any, Optional, Dict, List

# Lokale Imports
from core.speech_recognition import SpeechRecognizer
from core.text_to_speech import TextToSpeech
from core.command_processor import CommandProcessor
from core.autonomous_task_core import AutonomousTaskCore
from core.reinforcement_learning import ReinforcementLearningCore
from core.long_term_trainer import LongTermTrainer
from core.knowledge_expansion_agent import KnowledgeExpansionAgent
from core.plugin_manager import PluginManager
from core.knowledge_manager import KnowledgeManager
from core.crawler_client import CrawlerClient
from core.system_control import SystemControl
from core.system_monitor import SystemMonitor
from core.security_protocol import SecurityProtocolManager, PriorityLevel
from core.security_manager import SecurityManager
from core.learning_manager import LearningManager
from core.voice_biometrics import VoiceBiometricManager
from core.update_scheduler import UpdateScheduler
from webapp.server import WebInterfaceServer
from config.settings import Settings
from utils.logger import Logger
from utils.text_shortener import condense_text
from utils.error_reporter import ErrorReporter
from utils.authenticator import AuthenticatorManager
from utils.logger import Logger

GO_SERVICES = [
    {"name": "securityd", "cmd": ["go", "run", "./cmd/securityd"], "env": {}},
    {"name": "gatewayd", "cmd": ["go", "run", "./cmd/gatewayd"], "env": {}},
    {"name": "memoryd", "cmd": ["go", "run", "./cmd/memoryd"], "env": {}},
    {"name": "systemd", "cmd": ["go", "run", "./cmd/systemd"], "env": {}},
    {"name": "speechtaskd", "cmd": ["go", "run", "./cmd/speechtaskd"], "env": {}},
    {"name": "commandd", "cmd": ["go", "run", "./cmd/commandd"], "env": {}},
]


class HeadlessGUI:
    """Minimal Ersatz-GUI fuer headless Betrieb."""

    def __init__(self, jarvis: "JarvisAssistant", logger: Logger) -> None:
        self._jarvis = jarvis
        self._logger = logger

    def update_status(self, message: str) -> None:
        self._logger.info(f"[Status] {message}")

    def update_context_panels(self, **_kwargs) -> None:
        # Headless-Modus zeigt keine Kontexte an
        pass

    def handle_knowledge_progress(self, payload) -> None:
        self._logger.debug(f"[Knowledge] {payload}")

    def add_user_message(self, message: str) -> None:
        self._logger.info(f"[User] {message}")

    def add_assistant_message(self, message: str) -> None:
        self._logger.info(f"[Assistant] {message}")

    def show_message(self, title: str, message: str) -> None:
        self._logger.info(f"{title}: {message}")

    def run(self) -> None:
        self._logger.info("GUI nicht verfuegbar. Headless-Modus aktiv. Druecke STRG+C zum Beenden.")
        ready_cb = getattr(self._jarvis, "on_gui_ready", None)
        if callable(ready_cb):
            try:
                ready_cb()
            except Exception as exc:
                self._logger.debug("Remote-Ready Callback konnte nicht aufgerufen werden: %s", exc)
        while self._jarvis.is_running:
            time.sleep(0.5)


class WebInterfaceBridge(HeadlessGUI):
    """Bruecke zwischen Kernlogik und Weboberflaeche."""

    def update_status(self, message: str) -> None:
        super().update_status(message)
        try:
            runtime = self._jarvis.get_runtime_status()
            runtime["status_message"] = message
            self._jarvis._publish_remote_event("status", runtime)
        except Exception as exc:
            self._logger.debug("Status konnte nicht an Web-UI gesendet werden: %s", exc)

    def update_context_panels(self, **kwargs) -> None:
        super().update_context_panels(**kwargs)
        try:
            payload = {key: value for key, value in kwargs.items() if value is not None}
            self._jarvis._publish_remote_event("context_update", payload)
        except Exception as exc:
            self._logger.debug("Kontext konnte nicht an Web-UI gesendet werden: %s", exc)


class JarvisAssistant:
    """Hauptklasse faer den J.A.R.V.I.S. Assistenten"""

    def __init__(self):
        self.logger = Logger()
        self.settings = Settings()
        self.security_manager = SecurityManager(self.settings)
        self.authenticator = AuthenticatorManager(self.settings)
        self.is_running = False
        self.listening = False
        self._pending_security_request: Optional[dict] = None
        self._passphrase_attempts = 0
        self._passphrase_hint: Optional[str] = None
        self._min_command_words = 3
        self.remote_gateway = None
        self.web_interface = None
        self._conversation_history: List[Dict[str, Any]] = []
        self.system_monitor = SystemMonitor(update_interval=2.0)
        self.speech_thread: Optional[threading.Thread] = None
        self._pending_authenticator_payload: Optional[Dict[str, str]] = None
        self._desktop_cfg: Dict[str, Any] = {}
        self.desktop_app_enabled = False
        self.desktop_gui = None  # Referenz zum Desktop-Fenster

        # Komponenten initialisieren
        self.plugin_manager = PluginManager(self.logger)
        self.knowledge_manager = KnowledgeManager()
        self.crawler_client = CrawlerClient()
        self.system_control = SystemControl(self.security_manager, self.settings)
        self._go_processes: List[subprocess.Popen] = []
        self.tts = TextToSpeech(self.settings)
        self.task_core = AutonomousTaskCore(
            knowledge_manager=self.knowledge_manager,
            system_control=self.system_control,
            plugin_manager=self.plugin_manager,
            security_manager=self.security_manager,
            logger=self.logger,
        )

        self.speech_mode = "neutral"
        self.tts_stream_enabled = True
        try:
            self.tts.set_style(self.speech_mode)
        except Exception:
            pass

        self.learning_manager = LearningManager()
        self.reinforcement_core = ReinforcementLearningCore(self.learning_manager, logger=self.logger)
        self.long_term_trainer = LongTermTrainer(
            memory_manager=None,
            learning_manager=self.learning_manager,
            knowledge_manager=self.knowledge_manager,
            logger=self.logger,
        )
        knowledge_cfg = self.settings.get('knowledge', {}) if self.settings else {}
        expansion_cfg = knowledge_cfg.get('expansion', {}) if isinstance(knowledge_cfg, dict) else {}
        self.knowledge_agent = KnowledgeExpansionAgent(
            knowledge_manager=self.knowledge_manager,
            learning_manager=self.learning_manager,
            settings=expansion_cfg if isinstance(expansion_cfg, dict) else {},
            logger=self.logger,
        )
        self.voice_biometrics = VoiceBiometricManager()

        if self.authenticator and self.authenticator.needs_setup():
            needs_new_secret = not self.authenticator.setup_pending() or not self.authenticator.has_pending_secret()
            if needs_new_secret:
                try:
                    self._pending_authenticator_payload = self.authenticator.begin_setup()
                except Exception as exc:
                    self.logger.error("Authenticator-Setup konnte nicht vorbereitet werden: %s", exc)
                else:
                    self._persist_authenticator_payload(self._pending_authenticator_payload)
            else:
                self._pending_authenticator_payload = self.authenticator.get_pending_setup()
                self._persist_authenticator_payload(self._pending_authenticator_payload)
            self.logger.warning(
                "Authenticator-App fehlt: Öffne die Web-UI und hinterlege eine TOTP-App (z.B. Google Authenticator)."
            )
        elif self.authenticator:
            self._pending_authenticator_payload = self.authenticator.get_pending_setup()
            self._persist_authenticator_payload(self._pending_authenticator_payload)

        # LLM-Manager initialisieren (mit automatischer Modell-Installation)
        try:
            from core.llm_manager import LLMManager

            self.llm_manager = LLMManager(settings=self.settings)
            self.logger.info("LLM-Manager erfolgreich initialisiert")
        except Exception as e:
            self.logger.warning(f"LLM-Manager konnte nicht initialisiert werden: {e}")
            self.llm_manager = None

        self.security_protocol = SecurityProtocolManager(
            system_control=self.system_control,
            security_manager=self.security_manager,
            knowledge_manager=self.knowledge_manager,
            logger=self.logger,
            settings=self.settings,
            llm_manager=self.llm_manager,
            tts=self.tts,
        )

        self.command_processor = CommandProcessor(
            self.knowledge_manager,
            self.system_control,
            self.tts,
            self.plugin_manager,
            self.learning_manager,
            self.voice_biometrics,
            task_core=self.task_core,
            reinforcement_core=self.reinforcement_core,
            security_protocol=self.security_protocol,
            llm_manager=self.llm_manager,
            settings=self.settings,
        )
        try:
            self.long_term_trainer.set_command_processor(self.command_processor)
        except Exception:
            pass
        self.speech_recognizer = SpeechRecognizer(
            self.on_wake_word_detected,
            self.on_command_recognized,
            settings=self.settings,
        )
        try:
            speech_cfg = self.settings.get('speech', {}) or {}
            self.wake_word_enabled = bool(speech_cfg.get('wake_word_enabled', True))
            self._min_command_words = max(1, int(speech_cfg.get('min_command_words', 3)))
            self.tts_stream_enabled = bool(speech_cfg.get('stream_tts', True))
        except Exception:
            self.wake_word_enabled = True
            self._min_command_words = 3
            self.tts_stream_enabled = True
        try:
            security_cfg = self.settings.get('security', {}) if self.settings else {}
            if not isinstance(security_cfg, dict):
                security_cfg = {}
            auth_cfg = security_cfg.get('auth', {}) if isinstance(security_cfg, dict) else {}
            if not isinstance(auth_cfg, dict):
                auth_cfg = {}
            hint = auth_cfg.get('passphrase_hint')
            if isinstance(hint, str) and hint.strip():
                self._passphrase_hint = hint.strip()
        except Exception:
            self._passphrase_hint = None
        self.gui = self._initialise_gui()
        self.security_protocol.gui = self.gui

        self.knowledge_manager.register_progress_callback(self._handle_knowledge_progress)
        initial_plugin_context = dict(self.command_processor.context.get('plugin_context', {}) or {})
        cmd_map = self.command_processor.context.get('command_map')
        if cmd_map:
            initial_plugin_context['command_map'] = cmd_map
        self.gui.update_context_panels(
            use_case=self.command_processor.context.get('last_use_case'),
            scores=self.command_processor.context.get('use_case_scores'),
            plugin_context=initial_plugin_context,
        )
        self._initialise_remote_gateway()
        self._initialise_web_interface()

        try:
            security_cfg = self.settings.get('security', {}) if self.settings else {}
            if not isinstance(security_cfg, dict):
                security_cfg = {}
            automation_cfg = security_cfg.get('automation', {})
            if not isinstance(automation_cfg, dict):
                automation_cfg = {}
            if bool(automation_cfg.get('startup_diagnostics', True)):
                self.security_protocol.run_startup_check()
        except Exception as exc:
            self.logger.warning(f"Autodiagnose konnte nicht ausgefuehrt werden: {exc}")

        crawler_interval = getattr(getattr(self.crawler_client, "config", None), "sync_interval_sec", 1800)
        self.update_scheduler = UpdateScheduler(
            self.knowledge_manager,
            self.learning_manager,
            llm_manager=self.llm_manager,
            long_term_trainer=self.long_term_trainer,
            crawler_client=self.crawler_client,
            crawler_sync_interval=crawler_interval,
        )
        self.update_scheduler.start()

        self.logger.info("J.A.R.V.I.S. initialisiert")

    def _initialise_gui(self):
        """Initialisiert die Desktop- oder Web-UI."""
        try:
            desktop_cfg = self.settings.get('desktop_app', {}) or {}
        except Exception:
            desktop_cfg = {}
        try:
            web_cfg = self.settings.get('web_interface', {}) or {}
        except Exception:
            web_cfg = {}

        self._desktop_cfg = desktop_cfg if isinstance(desktop_cfg, dict) else {}
        self.desktop_app_enabled = bool(self._desktop_cfg.get("enabled") or os.getenv("JARVIS_DESKTOP"))
        web_enabled = bool(web_cfg.get("enabled")) if isinstance(web_cfg, dict) else False

        # Versuche Desktop-App zu laden
        if self.desktop_app_enabled:
            try:
                from desktop.jarvis_desktop_app import create_jarvis_desktop_gui
                self.desktop_gui = create_jarvis_desktop_gui(self)
                self.logger.info("Native Desktop-App (PyQt6) wird verwendet")
                return self.desktop_gui
            except Exception as exc:
                self.logger.warning("Desktop-App konnte nicht geladen werden, falle auf Web-Interface zurueck: %s", exc)

        # Fallback: Web-Interface
        if web_enabled:
            self.logger.info("Web-Interface wird verwendet")
            return WebInterfaceBridge(self, self.logger)

        # Fallback: Headless
        self.logger.info("Headless-Modus wird verwendet")
        return HeadlessGUI(self, self.logger)

    def _schedule_web_ui_open(self) -> None:
        try:
            web_cfg = self.settings.get('web_interface', {}) or {}
        except Exception as exc:
            self.logger.debug("Web-Interface Konfiguration konnte nicht gelesen werden: %s", exc)
            return
        if not isinstance(web_cfg, dict):
            return
        if not web_cfg.get("enabled", False):
            return
        if self.desktop_app_enabled and self._desktop_cfg.get("suppress_browser", True):
            self.logger.debug("Desktop-UI aktiv; automatisches Browser-Oeffnen uebersprungen.")
            return
        if not web_cfg.get("auto_open_browser", True):
            return
        if not self.web_interface:
            return

        host = str(web_cfg.get("host") or "127.0.0.1")
        port = int(web_cfg.get("port") or 8080)
        if host in ("0.0.0.0", "::", ""):
            host_for_url = "127.0.0.1"
        else:
            host_for_url = host
        url = f"http://{host_for_url}:{port}/"

        def _open_browser() -> None:
            try:
                if hasattr(self.web_interface, "wait_until_ready"):
                    self.web_interface.wait_until_ready(timeout=10.0)
            except Exception:
                pass
            time.sleep(0.3)
            try:
                opened = webbrowser.open(url, new=2)
                if opened:
                    self.logger.info("Web-UI im Browser geoeffnet: %s", url)
                else:
                    self.logger.debug("Browser konnte nicht automatisch geoeffnet werden (Rueckgabe False).")
            except Exception as exc:
                self.logger.debug("Web-UI konnte nicht automatisch geoeffnet werden: %s", exc)

        threading.Thread(target=_open_browser, name="JarvisWebAutoOpen", daemon=True).start()

    def _should_start_go_services(self) -> bool:
        env_flag = os.getenv("JARVIS_START_GO", "").strip().lower()
        if env_flag in {"1", "true", "yes"}:
            return True
        try:
            go_cfg = self.settings.get("go_services", {}) if self.settings else {}
            return bool(go_cfg.get("auto_start", False))
        except Exception:
            return False

    def _maybe_start_go_services(self) -> None:
        if not self._should_start_go_services():
            return
        go_root = Path(__file__).resolve().parent / "go"
        if not go_root.exists():
            return
        for svc in GO_SERVICES:
            name = svc.get("name")
            cmd = svc.get("cmd") or []
            if not cmd:
                continue
            try:
                proc = subprocess.Popen(
                    cmd,
                    cwd=str(go_root),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    env={**os.environ, **svc.get("env", {})},
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
                )
                self._go_processes.append(proc)
                self.logger.info("Go-Service '%s' gestartet (PID %s)", name, proc.pid)
            except Exception as exc:
                self.logger.warning("Go-Service '%s' konnte nicht gestartet werden: %s", name, exc)

    def _stop_go_services(self) -> None:
        for proc in self._go_processes:
            try:
                if proc.poll() is None:
                    proc.terminate()
            except Exception:
                pass
        self._go_processes.clear()

    def _initialise_remote_gateway(self) -> None:
        """Bereitet das WebSocket-Gateway gem. Settings vor."""
        try:
            remote_cfg = self.settings.get('remote_control', {}) or {}
        except Exception:
            remote_cfg = {}
        if not isinstance(remote_cfg, dict) or not remote_cfg.get('enabled'):
            self.remote_gateway = None
            return
        try:
            from core.websocket_gateway import RemoteCommandGateway

            self.remote_gateway = RemoteCommandGateway(self, remote_cfg, logger=self.logger)
            self.logger.info(
                "Remote-WebSocket vorbereitet (ws://%s:%s)",
                remote_cfg.get('host', '127.0.0.1'),
                remote_cfg.get('port', 8765),
            )
        except Exception as exc:
            self.logger.error(f"Remote-Control konnte nicht initialisiert werden: {exc}")
            self.remote_gateway = None

    def _initialise_web_interface(self) -> None:
        """Bereitet die Weboberflaeche vor."""
        try:
            web_cfg = self.settings.get('web_interface', {}) or {}
        except Exception:
            web_cfg = {}
        if not isinstance(web_cfg, dict) or not web_cfg.get('enabled'):
            self.web_interface = None
            return
        try:
            self.web_interface = WebInterfaceServer(self, web_cfg, logger=self.logger)
            self.logger.info(
                "Web-UI vorbereitet (http://%s:%s)",
                web_cfg.get('host', '0.0.0.0'),
                web_cfg.get('port', 8080),
            )
        except Exception as exc:
            self.logger.error(f"Web-Interface konnte nicht initialisiert werden: {exc}")
            self.web_interface = None

    def _publish_remote_event(self, event_type: str, payload: Optional[Dict[str, Any]] = None) -> None:
        targets = [getattr(self, "remote_gateway", None), getattr(self, "web_interface", None)]
        for target in targets:
            if not target:
                continue
            try:
                target.publish(event_type, payload or {})
            except Exception as exc:
                self.logger.debug("Remote-Event konnte nicht gesendet werden: %s", exc)

    def _emit_model_download_event(self, **payload) -> None:
        data = dict(payload or {})
        data.setdefault("timestamp", time.time())
        try:
            self._publish_remote_event("model_download_progress", data)
        except Exception as exc:
            self.logger.debug("Download-Event konnte nicht gesendet werden: %s", exc)

    def _post_to_main_thread(self, callback) -> bool:
        if self.desktop_gui and hasattr(self.desktop_gui, "post_to_qt"):
            try:
                self.desktop_gui.post_to_qt(callback)
                return True
            except Exception as exc:
                self.logger.debug("GUI Callback konnte nicht geplant werden: %s", exc)
        return False

    def on_gui_ready(self) -> None:
        """Wird aufgerufen sobald die GUI (oder Headless-Loop) laeuft."""
        if self.remote_gateway:
            self.remote_gateway.mark_ready()
        if self.web_interface:
            self.web_interface.mark_ready()
        self._publish_remote_event("status", {"state": "ready"})

    def get_runtime_status(self) -> Dict[str, Any]:
        """Liefert kompakten Status fuer Remote-Anfragen."""
        context = getattr(self.command_processor, 'context', {}) or {}
        status = {
            "running": self.is_running,
            "listening": self.listening,
            "speech_mode": self.speech_mode,
            "wake_word_enabled": getattr(self, "wake_word_enabled", True),
            "pending_security": bool(self._pending_security_request),
            "last_command": context.get('last_command'),
            "conversation_mode": context.get('conversation_mode'),
        }
        status["speech_status"] = self.get_speech_status()
        status["security"] = self.get_security_status()
        return status

    def get_context_snapshot(self) -> Dict[str, Any]:
        """Stellt Kontextinformationen fuer Webclients bereit."""
        context = dict(getattr(self.command_processor, 'context', {}) or {})
        plugin_context = dict(context.get('plugin_context', {}) or {})
        command_map = context.get('command_map')
        if command_map:
            plugin_context['command_map'] = command_map
        snapshot = {
            "use_case": context.get('last_use_case'),
            "scores": context.get('use_case_scores'),
            "plugin_context": plugin_context,
            "logic_path": context.get('logic_path'),
            "priority": context.get('priority'),
            "adaptive_context": context.get('adaptive_context'),
        }
        return snapshot

    # ------------------------------------------------------------------
    # Crawler-Integration
    # ------------------------------------------------------------------
    def get_crawler_status(self) -> Dict[str, Any]:
        client = getattr(self, "crawler_client", None)
        base = {
            "enabled": False,
            "connected": False,
            "jobs": [],
            "running_jobs": [],
            "completed_jobs": [],
            "last_sync": None,
            "documents_total": 0,
            "documents_24h": 0,
            "documents_since_sync": 0,
            "auto_sync": False,
            "recent_documents": [],
            "health": {},
            "config": {},
            "client_settings": {},
            "security": {},
        }
        if not client or not client.is_enabled():
            base["client_settings"] = self.get_crawler_client_settings()
            base["security"] = self.get_crawler_security_status()
            return base

        jobs: List[Dict[str, Any]] = []
        try:
            jobs = client.list_jobs()
        except Exception as exc:
            self.logger.warning("Crawler-Jobs konnten nicht geladen werden: %s", exc)
        running = [job for job in jobs if str(job.get("status")).lower() not in {"completed", "failed"}]
        completed = [job for job in jobs if str(job.get("status")).lower() == "completed"]
        health = client.get_health() or {}
        now = datetime.utcnow()
        total_docs = self.knowledge_manager.count_entries_by_source("web_crawler")
        docs_24h = self.knowledge_manager.count_entries_by_source_since("web_crawler", now - timedelta(hours=24))
        last_sync = client.load_last_sync()
        if last_sync:
            docs_since_sync = self.knowledge_manager.count_entries_by_source_since("web_crawler", last_sync)
        else:
            docs_since_sync = docs_24h
        recent_docs = self.get_crawler_documents(limit=50)
        base.update(
            {
                "enabled": True,
                "connected": bool(jobs) or bool(health),
                "jobs": jobs,
                "running_jobs": running,
                "completed_jobs": completed,
                "last_sync": last_sync.isoformat() if last_sync else None,
                "documents_total": total_docs,
                "documents_24h": docs_24h,
                "documents_since_sync": docs_since_sync,
                "auto_sync": bool(client.config.auto_sync),
                "recent_documents": recent_docs,
                "health": health,
                "config": self.get_crawler_service_config(),
                "client_settings": self.get_crawler_client_settings(),
                "security": self.get_crawler_security_status(),
            }
        )
        return base

    def get_crawler_documents(self, limit: int = 50, only_recent: bool = False) -> List[Dict[str, Any]]:
        since = datetime.utcnow() - timedelta(hours=24) if only_recent else None
        entries = self.knowledge_manager.fetch_entries_by_source("web_crawler", limit=limit, since=since)
        results: List[Dict[str, Any]] = []
        for entry in entries:
            snippet = condense_text(entry.get("content", ""), min_length=80, max_length=240)
            results.append(
                {
                    "id": entry.get("id"),
                    "title": entry.get("topic"),
                    "snippet": snippet,
                    "cached_at": entry.get("cached_at"),
                }
            )
        return results

    def start_crawler_job(self, topic: str, start_urls: List[str], max_pages: int, max_depth: int) -> Optional[int]:
        client = getattr(self, "crawler_client", None)
        if not client or not client.is_enabled():
            return None
        job_id = client.start_topic_job(topic, start_urls, max_pages, max_depth)
        if job_id:
            self._publish_remote_event(
                "crawler_event",
                {"type": "job_created", "topic": topic, "job_id": job_id, "status": "started"},
            )
        else:
            self._publish_remote_event(
                "crawler_event",
                {"type": "job_failed", "topic": topic},
            )
        return job_id

    def run_crawler_sync_now(self) -> Dict[str, Any]:
        if not self.update_scheduler:
            return {"imported": 0, "documents": 0}
        self._publish_remote_event("crawler_event", {"type": "sync_started"})
        try:
            result = self.update_scheduler.sync_crawler_now() or {"imported": 0, "documents": 0}
        except Exception as exc:
            self.logger.warning("Crawler Sync fehlgeschlagen: %s", exc)
            self._publish_remote_event("crawler_event", {"type": "sync_failed", "error": str(exc)})
            return {"imported": 0, "documents": 0, "error": str(exc)}
        self._publish_remote_event("crawler_event", {"type": "sync_completed", "result": result})
        return result

    def control_crawler(self, action: str) -> bool:
        client = getattr(self, "crawler_client", None)
        if not client:
            return False
        action = (action or "").lower()
        if action == "pause":
            success = client.pause_workers()
        elif action == "resume":
            success = client.resume_workers()
        else:
            success = False
        if success:
            self._publish_remote_event("crawler_event", {"type": f"worker_{action}"})
        return success

    def get_crawler_client_settings(self) -> Dict[str, Any]:
        try:
            crawler_cfg = dict(self.settings.get("crawler", {}))
        except Exception:
            crawler_cfg = {}
        return crawler_cfg

    def update_crawler_client_settings(self, payload: Dict[str, Any]) -> bool:
        if not isinstance(payload, dict):
            return False
        crawler_cfg = self.get_crawler_client_settings()
        crawler_cfg.update(
            {
                "enabled": bool(payload.get("enabled", crawler_cfg.get("enabled", True))),
                "base_url": str(payload.get("base_url", crawler_cfg.get("base_url", ""))),
                "api_key": payload.get("api_key", crawler_cfg.get("api_key", "")),
                "sync_interval_sec": int(payload.get("sync_interval_sec", crawler_cfg.get("sync_interval_sec", 1800))),
                "auto_sync": bool(payload.get("auto_sync", crawler_cfg.get("auto_sync", True))),
                "safe_mode": str(payload.get("safe_mode", crawler_cfg.get("safe_mode", "allow"))),
            }
        )
        self.settings.set("crawler", crawler_cfg)
        self.crawler_client.refresh_config()
        self._refresh_crawler_scheduler()
        return True

    def get_crawler_service_config(self) -> Dict[str, Any]:
        config_path = Path("services/crawler_service/config_crawler.json")
        if not config_path.exists():
            return {}
        try:
            return json.loads(config_path.read_text(encoding="utf-8"))
        except Exception as exc:
            self.logger.warning("Crawler-Konfiguration konnte nicht gelesen werden: %s", exc)
            return {}

    def update_crawler_service_config(self, payload: Dict[str, Any]) -> bool:
        if not isinstance(payload, dict):
            return False
        config_path = Path("services/crawler_service/config_crawler.json")
        current = self.get_crawler_service_config()
        if not current:
            current = {}
        for key in ["max_workers", "max_pages_per_job", "max_depth"]:
            if key in payload:
                try:
                    current[key] = int(payload[key])
                except Exception:
                    pass
        for section in ("resource_limits", "network"):
            if section in payload and isinstance(payload[section], dict):
                block = current.setdefault(section, {})
                block.update(payload[section])
        if "listen_host" in payload:
            current["listen_host"] = str(payload["listen_host"])
        if "listen_port" in payload:
            try:
                current["listen_port"] = int(payload["listen_port"])
            except Exception:
                pass
        if "data_dir" in payload:
            current["data_dir"] = str(payload["data_dir"])
        if "db_path" in payload:
            current["db_path"] = str(payload["db_path"])
        if "api_key" in payload:
            current["api_key"] = str(payload["api_key"])
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(json.dumps(current, indent=2), encoding="utf-8")
            return True
        except Exception as exc:
            self.logger.error("Crawler-Konfiguration konnte nicht gespeichert werden: %s", exc)
            return False

    def get_crawler_security_status(self) -> Dict[str, Any]:
        service_config = self.get_crawler_service_config()
        allowed_domains = service_config.get("network", {}).get("allowed_domains", [])
        return {
            "role": "crawler_service",
            "api_key_registered": bool(self.crawler_client and self.crawler_client.config.api_key),
            "domain_whitelist": bool(allowed_domains),
            "resource_guard": True,
            "safe_mode": self.get_crawler_client_settings().get("safe_mode", "allow"),
        }

    def set_crawler_safe_mode(self, mode: str) -> bool:
        crawler_cfg = self.get_crawler_client_settings()
        crawler_cfg["safe_mode"] = mode
        self.settings.set("crawler", crawler_cfg)
        self._publish_remote_event("crawler_event", {"type": "safe_mode", "value": mode})
        return True

    def _refresh_crawler_scheduler(self) -> None:
        if not self.update_scheduler or not self.crawler_client:
            return
        interval = getattr(self.crawler_client.config, "sync_interval_sec", 1800)
        try:
            self.update_scheduler._crawler_sync_interval = max(60, int(interval))
        except Exception:
            self.update_scheduler._crawler_sync_interval = 1800
        if not getattr(self.crawler_client.config, "auto_sync", True):
            self.update_scheduler._next_crawler_sync_at = None

    # ------------------------------------------------------------------
    # Sicherheitsstatus & Enrollment
    # ------------------------------------------------------------------
    def get_security_status(self) -> Dict[str, Any]:
        voice_cfg = self.settings.get('security.voice', {}) if self.settings else {}
        profiles_required = bool(voice_cfg.get('profiles_required', True))
        min_profiles = max(1, int(voice_cfg.get('min_profiles', 1) or 1))
        current_profiles = self.voice_biometrics.profile_count() if self.voice_biometrics else 0
        voice_missing = bool(profiles_required and current_profiles < min_profiles)
        self.requires_authenticator_setup()
        auth_status = self.authenticator.get_status() if self.authenticator else {}
        if auth_status is not None:
            auth_status = dict(auth_status)
            auth_status["needs_setup"] = self.requires_authenticator_setup()
            auth_status.setdefault(
                "pending_secret",
                self.authenticator.has_pending_secret() if self.authenticator else False,
            )
            if self._pending_authenticator_payload:
                auth_status.setdefault("pending_setup", dict(self._pending_authenticator_payload))
        policy_status = {}
        try:
            policy_status = self.security_manager.get_status()
        except Exception as exc:
            self.logger.debug("Security-Status konnte nicht gelesen werden: %s", exc)
        safe_mode = {}
        try:
            safe_mode = self.system_control.get_safe_mode_status()
        except Exception as exc:
            self.logger.debug("Safe-Mode-Status nicht verfuegbar: %s", exc)
        return {
            "authenticator": auth_status,
            "voice": {
                "required": profiles_required,
                "min_profiles": min_profiles,
                "profile_count": current_profiles,
                "needs_enrollment": voice_missing,
                "profiles": self.list_voice_profiles(),
            },
            "policy": policy_status,
            "safe_mode": safe_mode,
        }

    def set_security_profile(self, *, role: Optional[str] = None, level: Optional[str] = None) -> Dict[str, Any]:
        if role:
            try:
                self.security_manager.set_user_role(role)
            except Exception as exc:
                self.logger.warning("Rolle konnte nicht aktualisiert werden: %s", exc)
        if level:
            try:
                self.security_manager.update_security_level(level)
            except Exception as exc:
                self.logger.warning("Sicherheitsstufe konnte nicht aktualisiert werden: %s", exc)
        return self.get_security_status()

    def enter_safe_mode(self, reasons: Optional[List[str]] = None) -> Dict[str, Any]:
        try:
            result = self.system_control.enter_safe_mode(reasons=reasons or [])
        except Exception as exc:
            self.logger.error("Safe-Mode konnte nicht aktiviert werden: %s", exc)
            return {"error": str(exc)}
        return result

    def exit_safe_mode(self) -> Dict[str, Any]:
        try:
            return self.system_control.exit_safe_mode()
        except Exception as exc:
            self.logger.error("Safe-Mode konnte nicht deaktiviert werden: %s", exc)
            return {"error": str(exc)}

    def get_safe_mode_status(self) -> Dict[str, Any]:
        try:
            return self.system_control.get_safe_mode_status()
        except Exception as exc:
            self.logger.debug("Safe-Mode-Status konnte nicht gelesen werden: %s", exc)
            return {"active": False, "error": str(exc)}

    def requires_authenticator_setup(self) -> bool:
        if not self.authenticator:
            return False
        needs = self.authenticator.needs_setup()
        pending_payload = self.authenticator.get_pending_setup()
        if pending_payload:
            self._pending_authenticator_payload = dict(pending_payload)
            self._persist_authenticator_payload(self._pending_authenticator_payload)
        elif not needs:
            self._pending_authenticator_payload = None
            self._persist_authenticator_payload(None)
        return bool(needs)

    def begin_authenticator_setup(self) -> Dict[str, str]:
        if not self.authenticator:
            raise RuntimeError("Authenticator-Manager nicht verfuegbar")
        payload = self.authenticator.begin_setup()
        self._pending_authenticator_payload = dict(payload)
        self._persist_authenticator_payload(payload)
        return payload

    def confirm_authenticator_setup(self, code: str) -> bool:
        if not self.authenticator:
            return False
        success = self.authenticator.confirm_setup(code)
        if success:
            self._pending_authenticator_payload = None
            self._persist_authenticator_payload(None)
        return success

    def verify_authenticator_code(self, code: str) -> bool:
        if not self.authenticator:
            return False
        return self.authenticator.verify(code)

    def requires_voice_enrollment(self) -> bool:
        voice_cfg = self.settings.get('security.voice', {}) if self.settings else {}
        if not bool(voice_cfg.get('profiles_required', True)):
            return False
        min_profiles = max(1, int(voice_cfg.get('min_profiles', 1) or 1))
        current_profiles = self.voice_biometrics.profile_count() if self.voice_biometrics else 0
        return current_profiles < min_profiles

    def enroll_voice_profile(self, audio_blob: bytes, profile: str = "default") -> bool:
        if not self.voice_biometrics:
            return False
        return self.voice_biometrics.enroll_from_audio(audio_blob, profile=profile or "default")

    def list_voice_profiles(self) -> Dict[str, Dict[str, Any]]:
        if not self.voice_biometrics:
            return {}
        return self.voice_biometrics.list_profiles()

    def get_pending_authenticator_setup(self) -> Optional[Dict[str, str]]:
        return dict(self._pending_authenticator_payload) if self._pending_authenticator_payload else None

    def _persist_authenticator_payload(self, payload: Optional[Dict[str, Any]]) -> None:
        """Speichert das aktuelle Pending-Payload sicher auf der Platte.

        Die Daten werden bewusst ausserhalb des statischen Web-Verzeichnisses abgelegt,
        damit der TOTP-Secret nicht ohne Authentifizierung ausgelesen werden kann.
        """
        secure_root = Path("data") / "secure"
        legacy_target = Path(__file__).resolve().parent / "webapp" / "static" / "data" / "authenticator.json"
        try:
            secure_root.mkdir(parents=True, exist_ok=True)
            target = secure_root / "authenticator_pending.json"
            if not payload:
                if target.exists():
                    target.unlink()
                if legacy_target.exists():
                    legacy_target.unlink()
                return
            target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            if legacy_target.exists():
                legacy_target.unlink()
        except Exception as exc:
            self.logger.debug("Authenticator-Status konnte nicht persistiert werden: %s", exc)

    def get_conversation_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Gibt die letzten Chat-Meldungen zurueck."""
        if limit <= 0:
            return []
        snapshot = self._conversation_history[-limit:]
        return [dict(entry) for entry in snapshot]

    def get_system_metrics(self, include_details: bool = False) -> Dict[str, Any]:
        """Aggregiert System- und Hardwaredaten fuer das Web-Dashboard."""
        base_status = {}
        try:
            base_status = self.system_control.get_system_status()
        except Exception as exc:
            self.logger.debug("Systemstatus nicht verfuegbar: %s", exc)
        monitor_summary: Dict[str, Any] = {}
        monitor_details: Dict[str, Any] = {}
        if self.system_monitor:
            try:
                monitor_summary = self.system_monitor.get_system_summary(include_details=False)
                if include_details:
                    monitor_details = self.system_monitor.get_all_metrics()
            except Exception as exc:
                self.logger.debug("Systemmonitor konnte nicht abgefragt werden: %s", exc)
        return {
            "status": base_status,
            "summary": monitor_summary,
            "details": monitor_details if include_details else {},
        }

    def get_llm_status(self) -> Dict[str, Any]:
        manager = getattr(self, "llm_manager", None)
        if not manager:
            return {"available": {}, "current": None, "loaded": [], "active": False}
        try:
            available = manager.get_model_overview()
        except Exception:
            available = {}
        loaded = list(getattr(manager, "loaded_models", {}).keys())
        metadata = getattr(manager, "model_metadata", {})
        return {
            "available": available,
            "current": getattr(manager, "current_model", None),
            "loaded": loaded,
            "active": bool(getattr(manager, "model_loaded", False)),
            "metadata": metadata,
        }

    def control_llm_model(self, action: str, model_key: Optional[str] = None) -> Dict[str, Any]:
        manager = getattr(self, "llm_manager", None)
        if not manager:
            raise RuntimeError("LLM-Manager nicht verfuegbar.")
        model = (model_key or manager.current_model or "mistral").strip()
        action_normalized = (action or "").strip().lower()
        if action_normalized == "load":
            success = bool(manager.load_model(model))
            return {"action": "load", "success": success, "model": manager.current_model}
        if action_normalized == "unload":
            manager.unload_model()
            return {"action": "unload", "success": True}
        if action_normalized == "download":
            self._emit_model_download_event(model=model, status="starting")

            progress_state: Dict[str, Any] = {"status": "starting"}

            def _progress_cb(progress: Optional[Dict[str, Any]]) -> None:
                if not progress:
                    return
                event = dict(progress)
                event.setdefault("model", model)
                event.setdefault("status", "in_progress")
                progress_state["status"] = event.get("status", progress_state.get("status"))
                self._emit_model_download_event(**event)

            try:
                success = bool(manager.download_model(model, progress_cb=_progress_cb))
            except Exception as exc:
                self._emit_model_download_event(model=model, status="error", message=str(exc))
                raise
            else:
                if progress_state.get("status") == "already_exists":
                    self._emit_model_download_event(model=model, status="already_exists")
                    return {"action": "download", "success": success}
                status = "completed" if success else "failed"
                self._emit_model_download_event(model=model, status=status)
                return {"action": "download", "success": success}
        raise ValueError(f"Unbekannte Modellaktion: {action}")

    def get_training_snapshot(self) -> Dict[str, Any]:
        """Kompakte Übersicht aus Task-Core, Trainer und Lernsystemen."""
        snapshot = {
            "long_term": getattr(self.long_term_trainer, "last_summary", None),
            "knowledge": {},
            "learning": {},
            "autonomous_plan": None,
            "last_plan_result": None,
            "reinforcement": {},
        }
        try:
            snapshot["learning"] = self.learning_manager.get_snapshot()
        except Exception:
            snapshot["learning"] = {}
        try:
            snapshot["knowledge"] = self.knowledge_manager.get_knowledge_stats()
        except Exception:
            snapshot["knowledge"] = {}
        if self.task_core:
            plan = getattr(self.task_core, "active_plan", None)
            if plan:
                snapshot["autonomous_plan"] = plan.to_dict()
            result = getattr(self.task_core, "last_result", None)
            if result:
                snapshot["last_plan_result"] = result.to_dict()
        if self.reinforcement_core:
            try:
                snapshot["reinforcement"] = self.reinforcement_core.get_recent_feedback()
            except Exception:
                snapshot["reinforcement"] = {}
        return snapshot

    def run_training_cycle(self) -> Dict[str, Any]:
        """Loest optional den Long-Term-Trainer aus und liefert das Ergebnis."""
        result = None
        try:
            result = self.long_term_trainer.run_cycle()
        except Exception as exc:
            self.logger.warning("Training konnte nicht gestartet werden: %s", exc)
        return {"result": result}

    def get_settings_snapshot(self) -> Dict[str, Any]:
        speech = self.settings.get('speech', {}) or {}
        audio = self.settings.get('audio', {}) or {}
        models = self.settings.get('models', {}) or {}
        remote = self.settings.get('web_interface', {}) or {}
        desktop = self.settings.get('desktop_app', {}) or {}
        core_flags = {
            "debug_mode": bool(self.settings.get('debug_mode', False)),
            "auto_start": bool(self.settings.get('auto_start', False)),
        }
        return {
            "speech": speech,
            "audio": audio,
            "models": models,
            "web_interface": remote,
            "desktop_app": desktop,
            "core": core_flags,
        }

    def apply_settings_from_payload(self, payload: Dict[str, Any]) -> bool:
        """Uebernimmt Settings-Updates aus der Web-UI."""
        updated = False

        def _merge_dict(key: str, data: Dict[str, Any]) -> None:
            nonlocal updated
            if not isinstance(data, dict):
                return
            current = self.settings.get(key, {}) or {}
            if not isinstance(current, dict):
                current = {}
            merged = {**current, **data}
            self.settings.set(key, merged)
            updated = True

        for key in ("speech", "audio", "models", "web_interface", "desktop_app"):
            if key in payload and isinstance(payload[key], dict):
                _merge_dict(key, payload[key])

        core_cfg = payload.get("core")
        if isinstance(core_cfg, dict):
            if "debug_mode" in core_cfg:
                self.settings.set("debug_mode", bool(core_cfg["debug_mode"]))
                updated = True
            if "auto_start" in core_cfg:
                self.settings.set("auto_start", bool(core_cfg["auto_start"]))
                updated = True
        return updated

    def list_audio_devices(self) -> Dict[str, Any]:
        recognizer = getattr(self, "speech_recognizer", None)
        if not recognizer or not hasattr(recognizer, "enumerate_input_devices"):
            return {"devices": [], "selected": None}
        devices = []
        try:
            devices = recognizer.enumerate_input_devices()
        except Exception as exc:
            self.logger.debug("Audio-Geraete konnten nicht abgefragt werden: %s", exc)
        selected = {
            "name": getattr(recognizer.config, "input_device", None),
            "index": getattr(recognizer.config, "input_device_index", None),
        }
        return {"devices": devices, "selected": selected}

    def set_audio_device(self, *, name: Optional[str], index: Optional[int]) -> bool:
        recognizer = getattr(self, "speech_recognizer", None)
        if not recognizer or not hasattr(recognizer, "set_input_device"):
            return False
        try:
            recognizer.set_input_device(device_name=name, device_index=index)
            return True
        except Exception as exc:
            self.logger.error("Audio-Geraet konnte nicht gesetzt werden: %s", exc)
            return False

    def get_speech_status(self) -> Dict[str, Any]:
        recognizer = getattr(self, "speech_recognizer", None)
        available = bool(recognizer)
        try:
            enabled = recognizer.is_enabled() if available and hasattr(recognizer, "is_enabled") else True
        except Exception:
            enabled = True
        try:
            mode = getattr(recognizer, "mode", None)
        except Exception:
            mode = None
        return {
            "available": available,
            "enabled": bool(enabled),
            "listening": bool(self.listening),
            "wake_word_enabled": bool(getattr(self, "wake_word_enabled", True)),
            "speech_mode": self.speech_mode,
            "active_mode": mode,
        }

    def get_tts_settings(self) -> Dict[str, Any]:
        return {
            "stream_enabled": bool(getattr(self, "tts_stream_enabled", True)),
        }

    def set_tts_stream_enabled(self, enabled: bool) -> bool:
        normalized = bool(enabled)
        self.tts_stream_enabled = normalized
        try:
            self.settings.update_speech_settings(stream_tts=normalized)
        except Exception as exc:
            self.logger.debug("TTS-Stream-Einstellung konnte nicht gespeichert werden: %s", exc)
        return normalized

    def set_wake_word_enabled(self, enabled: bool) -> bool:
        normalized = bool(enabled)
        self.settings.update_speech_settings(wake_word_enabled=normalized)
        self.wake_word_enabled = normalized
        recognizer = getattr(self, "speech_recognizer", None)
        if recognizer and hasattr(recognizer, "set_wake_word_enabled"):
            try:
                recognizer.set_wake_word_enabled(normalized)
            except Exception as exc:
                self.logger.debug("Wake-Word konnte nicht aktualisiert werden: %s", exc)
        try:
            config = getattr(recognizer, "config", None)
            if config and hasattr(config, "wake_word_enabled"):
                config.wake_word_enabled = normalized  # type: ignore[attr-defined]
        except Exception:
            pass
        return normalized

    def get_knowledge_statistics(self) -> Dict[str, Any]:
        try:
            stats = self.knowledge_manager.get_knowledge_stats()
            return stats or {}
        except Exception as exc:
            self.logger.debug("Wissensstatistiken nicht verfuegbar: %s", exc)
            return {}

    def get_plugin_overview(self) -> List[Dict[str, Any]]:
        if not self.plugin_manager:
            return []
        try:
            return self.plugin_manager.get_plugin_overview()
        except Exception as exc:
            self.logger.debug("Plugin-Uebersicht nicht verfuegbar: %s", exc)
            return []

    def set_plugin_state(self, name: str, enabled: bool) -> bool:
        if not self.plugin_manager:
            return False
        try:
            return self.plugin_manager.set_plugin_enabled(name, enabled)
        except Exception as exc:
            self.logger.error("Plugin konnte nicht aktualisiert werden (%s): %s", name, exc)
            return False

    def reload_plugin(self, name: str) -> bool:
        if not self.plugin_manager:
            return False
        try:
            return self.plugin_manager.reload_plugin(name)
        except Exception as exc:
            self.logger.error("Plugin konnte nicht neu geladen werden (%s): %s", name, exc)
            return False

    def get_memory_snapshot(self, *, limit: int = 12, query: Optional[str] = None) -> Dict[str, Any]:
        memory_manager = getattr(self.knowledge_manager, "memory_manager", None)
        if not memory_manager:
            return {}
        recent: List[Dict[str, Any]] = []
        for entry in memory_manager.conversation_history[-max(1, limit):]:
            if not isinstance(entry, dict):
                continue
            item = dict(entry)
            timestamp_value = item.get("timestamp")
            if timestamp_value is not None and hasattr(timestamp_value, "isoformat"):
                try:
                    item["timestamp"] = timestamp_value.isoformat()
                except Exception:
                    item["timestamp"] = str(timestamp_value)
            recent.append(item)
        snapshot: Dict[str, Any] = {
            "short_term_summary": memory_manager.get_short_term_summary(),
            "active_topics": sorted(memory_manager.active_topics),
            "recent_messages": recent,
        }
        try:
            snapshot["conversation_context"] = memory_manager.get_conversation_context(
                max_messages=min(limit, 12),
                include_topics=True,
            )
        except Exception:
            snapshot["conversation_context"] = ""
        try:
            timeline = memory_manager.query_timeline(limit=min(limit, 20))
        except Exception:
            timeline = []
        if timeline:
            snapshot["timeline"] = timeline
        if query:
            try:
                snapshot["search_results"] = memory_manager.search_vector_memory(query, top_k=6)
            except Exception:
                snapshot["search_results"] = []
        return snapshot

    def list_custom_commands(self) -> List[Dict[str, Any]]:
        patterns = getattr(self.command_processor, "command_patterns", {}) or {}
        commands: List[Dict[str, Any]] = []
        for category, data in patterns.items():
            entries = list(data.get("patterns") or [])
            responses = list(data.get("responses") or [])
            for index, entry in enumerate(entries):
                pattern = str(entry or "").strip()
                if not pattern:
                    continue
                if responses:
                    response = responses[index] if index < len(responses) else responses[0]
                else:
                    response = ""
                commands.append(
                    {
                        "category": category,
                        "pattern": pattern,
                        "response": str(response),
                    }
                )
        return commands

    def add_custom_command_entry(self, pattern: str, response: str, *, category: str = "custom") -> bool:
        cleaned_pattern = str(pattern or "").strip()
        cleaned_response = str(response or "").strip()
        target_category = str(category or "custom").strip() or "custom"
        if not cleaned_pattern or not cleaned_response:
            raise ValueError("Pattern und Antwort duerfen nicht leer sein.")
        try:
            result = self.command_processor.add_custom_command(cleaned_pattern, cleaned_response, category=target_category)
            if result:
                self.logger.info("Benutzerdefinierter Befehl hinzugefuegt (%s)", target_category)
            return bool(result)
        except Exception as exc:
            self.logger.error("Benutzerdefinierter Befehl konnte nicht angelegt werden: %s", exc)
            return False

    def clear_logs(self) -> bool:
        try:
            log_file = Path("logs/jarvis.log")
            log_file.parent.mkdir(parents=True, exist_ok=True)
            log_file.write_text("", encoding="utf-8")
            self.logger.info("Logdatei wurde geleert.")
            return True
        except Exception as exc:
            self.logger.error("Logdatei konnte nicht geleert werden: %s", exc)
            return False

    def sample_audio_level(self, duration: float = 1.5) -> Optional[float]:
        recognizer = getattr(self, "speech_recognizer", None)
        if not recognizer or not hasattr(recognizer, "sample_input_level"):
            return None
        try:
            return recognizer.sample_input_level(duration=duration)
        except Exception:
            return None

    def execute_remote_command(self, text: str, *, metadata: Optional[Dict[str, Any]] = None, source="websocket", timeout: float = 45.0) -> str:
        """Fuehrt einen Remote-Befehl thread-sicher aus und liefert die Antwort."""
        future: Future = Future()
        metadata_snapshot = dict(metadata) if isinstance(metadata, dict) else {}

        def _run_command():
            try:
                result = self.send_text_command(text, metadata=metadata_snapshot, source=source)
            except Exception as exc:
                future.set_exception(exc)
            else:
                future.set_result(result)

        scheduled = self._post_to_main_thread(_run_command)
        if not scheduled:
            _run_command()
        return future.result(timeout)

    def _handle_knowledge_progress(self, payload):
        """Leitet Lernfortschritt an GUI und Web weiter."""
        try:
            self.gui.handle_knowledge_progress(payload)
        except Exception:
            pass
        normalized = payload if isinstance(payload, dict) else {"message": str(payload)}
        self._publish_remote_event("knowledge_progress", normalized)

    def _record_conversation_message(self, role: str, text: str, *, source: str = "unknown") -> None:
        entry = {
            "role": role,
            "text": text,
            "source": source,
            "timestamp": time.time(),
        }
        self._conversation_history.append(entry)
        if len(self._conversation_history) > 200:
            self._conversation_history = self._conversation_history[-200:]

    def _condense_response(self, text):
        try:
            cfg = self.settings.get('response', {}) or {}
            if not cfg.get('condense_enabled', True):
                return text
            content = (text or '').strip()
            if not content:
                return text
            # Dynamische Grenzen anhand Textlaenge
            length = len(content)
            min_chars = int(cfg.get('min_chars', 220))
            max_chars = int(cfg.get('max_chars', 800))
            if max_chars < min_chars:
                max_chars = min_chars
            dyn_max = min(max_chars, max(min_chars, int(length * 0.85)))
            dyn_min = min(max(min_chars, int(dyn_max * 0.6)), dyn_max)
            return condense_text(content, min_length=dyn_min, max_length=dyn_max)
        except Exception:
            return text

    def _deliver_response(self, response, *, fallback_message=None):
        """Bringt Antworten einheitlich in GUI und TTS ein."""
        fallback = fallback_message or "Entschuldigung, ich habe darauf keine passende Antwort gefunden."
        if isinstance(response, str):
            text = response.strip()
        else:
            text = str(response or '').strip()
        if not text:
            self.logger.info("Leere Antwort - verwende Fallback fuer Rueckmeldung")
            text = fallback
        prepared = self._condense_response(text)
        try:
            if self.tts_stream_enabled:
                self.tts.speak(prepared, style=self.speech_mode)
            else:
                self.logger.debug("TTS-Ausgabe uebersprungen (Stream deaktiviert)")
        except Exception as error:
            self.logger.error(f"TTS konnte Antwort nicht wiedergeben: {error}", exc_info=True)
            if hasattr(self.gui, "show_message"):
                try:
                    self.gui.show_message("Ausgabe fehlgeschlagen", prepared)
                except Exception:
                    self.logger.debug("GUI konnte Fehlermeldung nicht anzeigen")
        self.gui.add_assistant_message(prepared)
        self._record_conversation_message("assistant", prepared, source="assistant")
        self._publish_remote_event("assistant_message", {"text": prepared, "speech_mode": self.speech_mode})
        return prepared

    def activate_security_protocol(self, level=None, reason="Manuell ausgelöst", *, initiated_by="assistant"):
        """Startet das Sicherheits-Notfallprotokoll und gibt den Vorfallsdatensatz zurück."""
        incident = self.security_protocol.activate(level, reason, initiated_by=initiated_by)
        final_message = None
        if isinstance(getattr(incident, "results", None), dict):
            final_message = incident.results.get("final_message")
        if final_message and isinstance(final_message, str):
            try:
                self.gui.update_status(final_message)
            except Exception:
                pass
        return incident

    def _infer_mode_from_emotion(self, emotion: dict) -> Optional[str]:
        label = (emotion or {}).get("label", "").lower().strip()
        if not label:
            return None
        confidence = float((emotion or {}).get("confidence") or 0.0)
        if confidence < 0.2:
            return None
        mapping = {
            "happy": "freundlich",
            "excited": "humorvoll",
            "confident": "professionell",
            "focused": "professionell",
            "expressive": "freundlich",
            "calm": "neutral",
            "uncertain": "freundlich",
            "neutral": "neutral",
        }
        return mapping.get(label)

    def _set_speech_mode(self, mode: str) -> None:
        mode_normalized = (mode or "neutral").strip().lower()
        if not mode_normalized:
            mode_normalized = "neutral"
        if mode_normalized == self.speech_mode:
            return
        self.speech_mode = mode_normalized
        try:
            self.tts.set_style(mode_normalized)
        except Exception as exc:
            self.logger.debug(f"Sprachmodus konnte nicht gesetzt werden: {exc}")

    def _handle_command(self, command_text, *, fallback_message=None, mark_listening_done=False, emotion=None, audio_blob=None, metadata_override=None):
        """Verarbeitet einen Befehl mit freundlicher Rueckmeldung."""
        self.gui.update_status("Verarbeite Befehl...")
        self._publish_remote_event("status", {"state": "processing", "command": command_text})
        fallback = fallback_message or "Entschuldigung, ich habe darauf keine passende Antwort gefunden."
        response = None
        metadata = {}
        if emotion:
            metadata["emotion"] = emotion
            inferred_mode = self._infer_mode_from_emotion(emotion)
            if inferred_mode:
                self._set_speech_mode(inferred_mode)
        if self.speech_mode:
            metadata["speech_mode"] = self.speech_mode
        if audio_blob:
            metadata["audio_blob"] = audio_blob
        if metadata_override:
            try:
                metadata.update(metadata_override)
            except Exception:
                metadata_override = {}
        metadata_for_pending = dict(metadata)
        try:
            response = self.command_processor.process_command(command_text, metadata=metadata)
        except Exception as error:
            self.logger.error(f"Fehler bei der Befehlsverarbeitung: {error}", exc_info=True)
            response = f"Bei der Verarbeitung ist ein Fehler aufgetreten: {error}"
        delivered = None
        try:
            delivered = self._deliver_response(response, fallback_message=fallback)
        finally:
            self.gui.update_status("Bereit")
            if mark_listening_done:
                self.listening = False
            self._publish_remote_event("status", {"state": "idle"})
        voice_mode_hint = self.command_processor.context.get('voice_mode')
        if voice_mode_hint:
            self._set_speech_mode(voice_mode_hint)
        plugin_context = dict(self.command_processor.context.get('plugin_context', {}) or {})
        command_map = self.command_processor.context.get('command_map')
        if command_map:
            plugin_context['command_map'] = command_map
        self.gui.update_context_panels(
            use_case=self.command_processor.context.get('last_use_case'),
            scores=self.command_processor.context.get('use_case_scores'),
            plugin_context=plugin_context,
        )
        pending_security = self.command_processor.context.get('pending_high_risk_authorization')
        if pending_security:
            payload = dict(pending_security)
            payload['metadata'] = dict(metadata_for_pending)
            payload['emotion'] = emotion
            payload['audio_blob'] = audio_blob
            if payload.get('hint') is None and self._passphrase_hint:
                payload['hint'] = self._passphrase_hint
            self._pending_security_request = payload
            try:
                self._passphrase_attempts = int(payload.get('attempts', 0))
            except Exception:
                self._passphrase_attempts = 0
            sanitized_payload = dict(payload)
            sanitized_payload.pop('audio_blob', None)
            metadata_copy = sanitized_payload.get('metadata') or {}
            if isinstance(metadata_copy, dict):
                metadata_copy.pop('audio_blob', None)
                sanitized_payload['metadata'] = metadata_copy
            self._publish_remote_event("security_challenge", {**sanitized_payload, "active": True})
        else:
            self._pending_security_request = None
            self._passphrase_attempts = 0
            try:
                self.command_processor.context['pending_high_risk_authorization'] = None
            except Exception:
                pass
            self._publish_remote_event("security_challenge", {"active": False})
        return delivered

    def _get_last_emotion_snapshot(self):
        try:
            return self.speech_recognizer.get_last_emotion()
        except Exception:
            return {}

    def _get_last_audio_blob(self):
        try:
            return self.speech_recognizer.get_last_audio_blob()
        except Exception:
            return None

    def _is_voice_command_valid(self, text: str) -> bool:
        words = [token for token in (text or '').split() if token]
        if len(words) >= max(1, self._min_command_words):
            return True
        context = getattr(self.command_processor, 'context', {}) or {}
        if context.get('pending_clarification') or context.get('pending_confirmation'):
            return True
        return False

    def _handle_passphrase_attempt(self, text: str, emotion: Optional[dict], audio_blob):
        pending = self._pending_security_request
        if not pending:
            return "Keine Sicherheitsfreigabe aktiv."
        cleaned = (text or '').strip()
        processor = self.command_processor
        if not cleaned:
            msg = 'Ich habe keine Passphrase erkannt.'
            self.tts.speak(msg)
            self._publish_remote_event("security_result", {"status": "empty"})
            return msg
        if not processor.has_passphrase():
            msg = 'Es ist keine Passphrase konfiguriert. Bitte richte eine Passphrase in den Sicherheitseinstellungen ein.'
            self.tts.speak(msg)
            processor.context['pending_high_risk_authorization'] = None
            self._pending_security_request = None
            self._passphrase_attempts = 0
            self._publish_remote_event("security_result", {"status": "missing_passphrase"})
            return msg
        if not processor.validate_passphrase(cleaned):
            self._passphrase_attempts += 1
            hint = pending.get('hint') or self._passphrase_hint
            if self._passphrase_attempts >= 3:
                msg = 'Passphrase falsch. Der Vorgang wurde abgebrochen.'
                self.tts.speak(msg)
                processor.context['pending_high_risk_authorization'] = None
                self._pending_security_request = None
                self._passphrase_attempts = 0
            else:
                if hint:
                    msg = f'Passphrase nicht erkannt. Hinweis: {hint}.'
                    self.tts.speak(msg)
                else:
                    msg = 'Passphrase nicht erkannt. Bitte versuche es erneut.'
                    self.tts.speak(msg)
            self._publish_remote_event(
                "security_result",
                {"status": "failed", "attempts": self._passphrase_attempts, "hint_available": bool(self._passphrase_hint)},
            )
            return msg
        msg = 'Passphrase akzeptiert.'
        self.tts.speak(msg)
        metadata = dict(pending.get('metadata') or {})
        metadata['passphrase_ok'] = True
        metadata.pop('audio_blob', None)
        processor.context['pending_high_risk_authorization'] = None
        self._pending_security_request = None
        self._passphrase_attempts = 0
        self._publish_remote_event("security_result", {"status": "accepted"})
        original_command = pending.get('command')
        if not original_command:
            return msg
        stored_emotion = pending.get('emotion') or emotion
        stored_audio = pending.get('audio_blob') if pending.get('audio_blob') is not None else audio_blob
        self._handle_command(
            original_command,
            mark_listening_done=True,
            emotion=stored_emotion,
            audio_blob=stored_audio,
            metadata_override=metadata,
        )
        return msg

    def start(self):
        """Startet den Assistenten"""
        self.is_running = True
        self.logger.info("J.A.R.V.I.S. wird gestartet...")
        self._maybe_start_go_services()
        if self.remote_gateway:
            self.remote_gateway.mark_not_ready()
            self.remote_gateway.start()
        if self.web_interface:
            self.web_interface.mark_not_ready()
            self.web_interface.start()
            self._schedule_web_ui_open()

        # Debug-Modus bei erstem Start
        if self.settings.get('first_run', True):
            self.run_debug_mode()
            self.settings.set('first_run', False)

        # Spracherkennung aktivieren
        self.start_listening()

        self.gui.update_status("Bereit")

        # GUI starten (blockiert den Hauptthread)
        self.gui.run()

    def stop(self):
        """Stoppt den Assistenten"""
        self.is_running = False
        self.stop_listening()
        # TTS sauber herunterfahren (Worker-Thread stoppen, Engine freigeben)
        try:
            if hasattr(self, "tts") and self.tts:
                self.tts.shutdown()
        except Exception:
            pass
        if self.plugin_manager:
            self.plugin_manager.shutdown()
        if hasattr(self, "update_scheduler") and self.update_scheduler:
            self.update_scheduler.stop()
        try:
            self.system_control.exit_safe_mode()
        except Exception:
            pass
        if self.remote_gateway:
            try:
                self.remote_gateway.stop()
            except Exception as exc:
                self.logger.debug("Remote-Gateway konnte nicht sauber gestoppt werden: %s", exc)
        if self.web_interface:
            try:
                self.web_interface.stop()
            except Exception as exc:
                self.logger.debug("Web-Interface konnte nicht sauber gestoppt werden: %s", exc)
        self.logger.info("J.A.R.V.I.S. wird beendet")
        self._stop_go_services()

    def run_debug_mode(self):
        """Faehrt Systempraefungen beim ersten Start durch"""
        self.logger.info("Debug-Modus: Systempraefungen werden durchgefuehrt...")

        # VOSK Modell praefen
        recognizer_enabled = True
        if hasattr(self.speech_recognizer, "is_enabled"):
            try:
                recognizer_enabled = bool(self.speech_recognizer.is_enabled())
            except Exception:
                recognizer_enabled = True
        if recognizer_enabled:
            if not self.speech_recognizer.check_model():
                self.tts.speak("Sprachmodell fehlt. Bitte lade das deutsche Modell herunter.")
                self.gui.show_message("Sprachmodell fehlt", "Das deutsche Sprachmodell muss heruntergeladen werden.")
        else:
            self.logger.info("Spracherkennung ist deaktiviert; ueberspringe Modellpruefung.")

        # Mikrofon praefen
        if not self.speech_recognizer.test_microphone():
            self.tts.speak("Mikrofon nicht verfaegbar.")
            self.gui.show_message("Mikrofon-Fehler", "Das Mikrofon ist nicht verfaegbar.")

        # TTS praefen
        self.tts.speak("Systempraefung abgeschlossen. J.A.R.V.I.S. ist bereit.")
        self.gui.update_status("Bereit")
        self.logger.info("Debug-Modus abgeschlossen")

    def on_wake_word_detected(self):
        """Callback wenn Wake-Word erkannt wird"""
        if self.is_running:
            self.listening = True
            if getattr(self, "wake_word_enabled", True):
                try:
                    self.tts.speak("Ja, ich haere.")
                except Exception as exc:
                    self.logger.error(f"Akustische Rueckmeldung fehlgeschlagen: {exc}")
                self.gui.update_status("Haere zu...")
                self.logger.info("Wake-Word erkannt, haere zu...")
            else:
                self.gui.update_status("Spracherkennung aktiv")
                self.logger.info("Sprachaufnahme gestartet (ohne Wake-Word).")

    def on_command_recognized(self, command_text):
        """Callback wenn Befehl erkannt wird"""
        if not self.is_running:
            return
        cleaned = (command_text or '').strip()
        emotion = self._get_last_emotion_snapshot()
        audio_blob = self._get_last_audio_blob()
        if self._pending_security_request:
            self.logger.info('Passphrase-Versuch registriert.')
            self._handle_passphrase_attempt(cleaned, emotion, audio_blob)
            return
        if not cleaned:
            self.logger.info('Leerer Sprachbefehl erkannt')
            self.gui.update_status('Bereit')
            self.listening = False
            return
        if not self._is_voice_command_valid(cleaned):
            self.logger.info('Verwerfe zu kurzen Sprachbefehl: %s', cleaned)
            self.tts.speak(f'Bitte formuliere deinen Befehl mit mindestens {self._min_command_words} Woertern.')
            self.gui.update_status('Bitte klaren Befehl geben')
            self.listening = False
            return
        self.logger.info('Befehl erkannt: %s', cleaned)
        self.gui.add_user_message(cleaned)
        self._record_conversation_message("user", cleaned, source="speech")
        self._publish_remote_event("user_message", {"text": cleaned, "source": "speech"})
        self._handle_command(cleaned, mark_listening_done=True, emotion=emotion, audio_blob=audio_blob)

    def run_workflow(self, workflow_definition, *, confirm=False, dry_run=False):
        """Fuehrt einen definierten Workflow ueber die Systemsteuerung aus."""
        return self.system_control.run_workflow(workflow_definition, confirm=confirm, dry_run=dry_run)

    def create_directory(self, directory, **kwargs):
        """Delegiert an SystemControl.create_directory."""
        return self.system_control.create_directory(directory, **kwargs)

    def create_file(self, file_path, **kwargs):
        """Delegiert an SystemControl.create_file."""
        return self.system_control.create_file(file_path, **kwargs)

    def rename_path(self, source, destination, **kwargs):
        """Delegiert an SystemControl.rename_path."""
        return self.system_control.rename_path(source, destination, **kwargs)

    def copy_path(self, source, destination, **kwargs):
        """Delegiert an SystemControl.copy_path."""
        return self.system_control.copy_path(source, destination, **kwargs)

    def move_path(self, source, destination, **kwargs):
        """Delegiert an SystemControl.move_path."""
        return self.system_control.move_path(source, destination, **kwargs)

    def delete_path(self, target_path, **kwargs):
        """Delegiert an SystemControl.delete_path."""
        return self.system_control.delete_path(target_path, **kwargs)

    def run_shell_command(self, command_name, **kwargs):
        """Delegiert an SystemControl.run_shell_command."""
        return self.system_control.run_shell_command(command_name, **kwargs)

    def execute_script(self, script_identifier, **kwargs):
        """Delegiert an SystemControl.execute_script."""
        return self.system_control.execute_script(script_identifier, **kwargs)

    def send_text_command(self, text, *, metadata: Optional[Dict[str, Any]] = None, source: str = "text") -> str:
        """Verarbeitet Textbefehle (GUI oder Remote) und liefert Antwort."""
        cleaned_text = (text or '').strip()
        if not cleaned_text:
            return "Kein Textbefehl uebermittelt."
        if self._pending_security_request:
            self.logger.info('Passphrase-Eingabe (Text) registriert.')
            result = self._handle_passphrase_attempt(
                cleaned_text,
                emotion=None,
                audio_blob=self._pending_security_request.get('audio_blob') if self._pending_security_request else None,
            )
            return result or "Passphrase-Eingabe verarbeitet."
        self.logger.info('Text-Befehl (%s): %s', source, cleaned_text)
        self.gui.add_user_message(cleaned_text)
        self._record_conversation_message("user", cleaned_text, source=source)
        self._publish_remote_event("user_message", {"text": cleaned_text, "source": source})
        metadata_payload = dict(metadata) if isinstance(metadata, dict) else {}
        response = self._handle_command(cleaned_text, metadata_override=metadata_payload)
        return response or ""

    def start_listening(self) -> bool:
        """Aktiviert die kontinuierliche Spracherkennung."""
        recognizer = getattr(self, "speech_recognizer", None)
        if not recognizer:
            self.listening = False
            self.logger.info("Spracherkennung ist nicht initialisiert.")
            return False
        try:
            enabled = recognizer.is_enabled() if hasattr(recognizer, "is_enabled") else True
        except Exception:
            enabled = True
        if not enabled:
            self.listening = False
            self.logger.info("Spracherkennung ist deaktiviert; Start wird uebersprungen.")
            try:
                self.gui.update_status("Spracherkennung deaktiviert")
            except Exception:
                pass
            return False
        self.listening = True
        if getattr(self, "speech_thread", None) and self.speech_thread.is_alive():
            try:
                if hasattr(recognizer, "is_listening"):
                    recognizer.is_listening = True  # type: ignore[attr-defined]
            except Exception:
                pass
            return True
        self.speech_thread = threading.Thread(target=recognizer.start_listening, daemon=True)
        self.speech_thread.start()
        return True

    def stop_listening(self) -> bool:
        """Stoppt die laufende Spracherkennung."""
        self.listening = False
        recognizer = getattr(self, "speech_recognizer", None)
        if not recognizer:
            return False
        try:
            recognizer.stop_listening()
        except Exception as exc:
            self.logger.debug("Spracherkennung konnte nicht gestoppt werden: %s", exc)
            return False
        try:
            if hasattr(recognizer, "is_listening"):
                recognizer.is_listening = False  # type: ignore[attr-defined]
        except Exception:
            pass
        try:
            if hasattr(self, "speech_thread") and self.speech_thread and self.speech_thread.is_alive():
                self.speech_thread.join(timeout=1.5)
        except Exception:
            pass
        return True

    def process_input(self, text):
        """Verarbeitet eine Chat-Eingabe aus der GUI."""
        message = (text or '').strip()
        if not message:
            return "Bitte gib einen Text ein."

        self.logger.info(f"Chat-Eingabe: {message}")
        self.gui.update_status("Verarbeite Eingabe...")

        try:
            response = self.command_processor.process_command(message, metadata={"speech_mode": self.speech_mode})
        except Exception as error:
            self.logger.error(f"Fehler bei der Chat-Verarbeitung: {error}", exc_info=True)
            response = f"Fehler: {error}"
        finally:
            self.gui.update_status("Bereit")

        response_text = response if isinstance(response, str) else str(response)

        if response_text:
            try:
                self.tts.speak(response_text, style=self.speech_mode)
            except Exception as tts_error:
                self.logger.error(f"TTS-Ausgabe fehlgeschlagen: {tts_error}", exc_info=True)

        plugin_context = dict(self.command_processor.context.get('plugin_context', {}) or {})
        cmd_map = self.command_processor.context.get('command_map')
        if cmd_map:
            plugin_context['command_map'] = cmd_map
        self.gui.update_context_panels(
            use_case=self.command_processor.context.get('last_use_case'),
            scores=self.command_processor.context.get('use_case_scores'),
            plugin_context=plugin_context,
        )
        return response_text

    # ------------------------------------------------------------------
    # Feedback / Reinforcement
    # ------------------------------------------------------------------
    def record_feedback(self, score: float, message: str, *, correction: Optional[str] = None, intent: Optional[str] = None) -> Dict[str, Any]:
        entry: Dict[str, Any] = {}
        try:
            entry = self.learning_manager.record_feedback(score, message, correction=correction, intent=intent)
        except Exception as exc:
            self.logger.warning("Feedback konnte nicht gespeichert werden: %s", exc)
        if self.reinforcement_core:
            try:
                self.reinforcement_core.register_feedback(entry)
            except Exception:
                pass
        try:
            if correction is not None and hasattr(self.knowledge_manager, "add_user_feedback"):
                self.knowledge_manager.add_user_feedback(message, message, score, correction or "")
        except Exception:
            pass
        return entry

    def get_last_assistant_message(self) -> Optional[str]:
        history = getattr(self, "_conversation_history", []) or []
        for item in reversed(history):
            if not isinstance(item, dict):
                continue
            if "assistant" in item:
                return item.get("assistant")
        return None


def main():
    """Hauptfunktion"""
    try:
        # ueberpruefen ob alle erforderlichen Verzeichnisse existieren
        os.makedirs("data", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        os.makedirs("models", exist_ok=True)
        # Debug-Logging aktivieren (Konsole & Datei)
        from utils.logger import Logger
        Logger().set_level("DEBUG")
        print("Debug-Logs: logs/jarvis.log")

        # Globalen Fehler-Reporter aktivieren (respektiert Settings.telemetry)
        try:
            settings_for_reporting = Settings()
            ErrorReporter(settings_for_reporting).install_global_hook()
        except Exception as _err:
            # Niemals Start verhindern
            Logger().warning(f"Fehler-Reporter konnte nicht installiert werden: {_err}")

        # J.A.R.V.I.S. starten
        jarvis = JarvisAssistant()
        jarvis.start()

    except KeyboardInterrupt:
        print("\nJ.A.R.V.I.S. wird beendet...")
    except Exception as e:
        print(f"Fehler beim Start: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
