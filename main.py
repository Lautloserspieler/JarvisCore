#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
J.A.R.V.I.S. - Deutscher KI-Sprachassistent
Hauptmodul für den Start der Anwendung
Unterstützt Desktop UI (Dear ImGui), Web UI (FastAPI/React) oder Headless-Modus
"""

import sys
import os
import threading
import time
import webbrowser
import json
import subprocess
import uvicorn
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
from config.settings import Settings
from utils.logger import Logger
from utils.text_shortener import condense_text
from utils.error_reporter import ErrorReporter
from utils.authenticator import AuthenticatorManager

GO_SERVICES = [
    {"name": "securityd", "cmd": ["go", "run", "./cmd/securityd"], "env": {}},
    {"name": "gatewayd", "cmd": ["go", "run", "./cmd/gatewayd"], "env": {}},
    {"name": "memoryd", "cmd": ["go", "run", "./cmd/memoryd"], "env": {}},
    {"name": "systemd", "cmd": ["go", "run", "./cmd/systemd"], "env": {}},
    {"name": "speechtaskd", "cmd": ["go", "run", "./cmd/speechtaskd"], "env": {}},
    {"name": "commandd", "cmd": ["go", "run", "./cmd/commandd"], "env": {}},
]


class HeadlessGUI:
    """Minimal Ersatz-GUI für headless Betrieb."""

    def __init__(self, jarvis: "JarvisAssistant", logger: Logger) -> None:
        self._jarvis = jarvis
        self._logger = logger

    def update_status(self, message: str) -> None:
        self._logger.info(f"[Status] {message}")

    def update_context_panels(self, **_kwargs) -> None:
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
        self._logger.info("GUI nicht verfügbar. Headless-Modus aktiv. Drücke STRG+C zum Beenden.")
        ready_cb = getattr(self._jarvis, "on_gui_ready", None)
        if callable(ready_cb):
            try:
                ready_cb()
            except Exception as exc:
                self._logger.debug("Remote-Ready Callback konnte nicht aufgerufen werden: %s", exc)
        while self._jarvis.is_running:
            time.sleep(0.5)


class WebInterfaceBridge(HeadlessGUI):
    """Brücke zwischen Kernlogik und Weboberfläche."""

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
    """Hauptklasse für den J.A.R.V.I.S. Assistenten"""

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
        self.desktop_gui = None
        self._web_ui_thread: Optional[threading.Thread] = None
        self._web_server: Optional[uvicorn.Server] = None

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

        # LLM-Manager initialisieren
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
        """Initialisiert die Desktop-UI (Dear ImGui FULL VERSION) oder Headless-Modus."""
        try:
            desktop_cfg = self.settings.get('desktop_app', {}) or {}
        except Exception:
            desktop_cfg = {}

        self._desktop_cfg = desktop_cfg if isinstance(desktop_cfg, dict) else {}
        self.desktop_app_enabled = bool(self._desktop_cfg.get("enabled") or os.getenv("JARVIS_DESKTOP"))

        # Versuche Dear ImGui Desktop-App FULL VERSION zu laden
        if self.desktop_app_enabled:
            try:
                from desktop.jarvis_imgui_app_full import create_jarvis_imgui_gui_full
                self.desktop_gui = create_jarvis_imgui_gui_full(self)
                self.logger.info("🎮 Dear ImGui Desktop-App FULL geladen (7 Tabs, GPU-beschleunigt)")
                return self.desktop_gui
            except ImportError as exc:
                self.logger.warning("Dear ImGui nicht verfügbar (%s), falle auf Headless zurück", exc)
                self.logger.info("Installiere mit: pip install dearpygui")
            except Exception as exc:
                self.logger.warning("Desktop-App konnte nicht geladen werden: %s", exc)

        # Fallback: Headless
        self.logger.info("Headless-Modus wird verwendet")
        return HeadlessGUI(self, self.logger)

    def _persist_authenticator_payload(self, payload: Optional[Dict[str, Any]]) -> None:
        """Speichert das aktuelle Pending-Payload sicher auf der Platte."""
        secure_root = Path("data") / "secure"
        try:
            secure_root.mkdir(parents=True, exist_ok=True)
            target = secure_root / "authenticator_pending.json"
            if not payload:
                if target.exists():
                    target.unlink()
                return
            target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as exc:
            self.logger.debug("Authenticator-Status konnte nicht persistiert werden: %s", exc)

    def _handle_knowledge_progress(self, payload):
        """Leitet Lernfortschritt an GUI und Web weiter."""
        try:
            self.gui.handle_knowledge_progress(payload)
        except Exception:
            pass
        normalized = payload if isinstance(payload, dict) else {"message": str(payload)}
        self._publish_remote_event("knowledge_progress", normalized)

    def _schedule_web_ui_open(self) -> None:
        pass

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
        return False

    def on_gui_ready(self) -> None:
        if self.remote_gateway:
            self.remote_gateway.mark_ready()
        if self.web_interface:
            self.web_interface.mark_ready()
        self._publish_remote_event("status", {"state": "ready"})

    def get_runtime_status(self) -> Dict[str, Any]:
        context = getattr(self.command_processor, 'context', {}) or {}
        return {
            "running": self.is_running,
            "listening": self.listening,
            "speech_mode": self.speech_mode,
            "wake_word_enabled": getattr(self, "wake_word_enabled", True),
            "pending_security": bool(self._pending_security_request),
            "last_command": context.get('last_command'),
            "conversation_mode": context.get('conversation_mode'),
        }

    def get_context_snapshot(self) -> Dict[str, Any]:
        context = dict(getattr(self.command_processor, 'context', {}) or {})
        plugin_context = dict(context.get('plugin_context', {}) or {})
        command_map = context.get('command_map')
        if command_map:
            plugin_context['command_map'] = command_map
        return {
            "use_case": context.get('last_use_case'),
            "scores": context.get('use_case_scores'),
            "plugin_context": plugin_context,
            "logic_path": context.get('logic_path'),
            "priority": context.get('priority'),
            "adaptive_context": context.get('adaptive_context'),
        }

    def get_security_status(self) -> Dict[str, Any]:
        return {"status": "ok"}

    def get_speech_status(self) -> Dict[str, Any]:
        return {"available": True, "listening": self.listening}

    def get_system_metrics(self, include_details: bool = False) -> Dict[str, Any]:
        base_status = {}
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
            raise RuntimeError("LLM-Manager nicht verfügbar.")
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
            try:
                success = bool(manager.download_model(model))
            except Exception as exc:
                self._emit_model_download_event(model=model, status="error", message=str(exc))
                raise
            else:
                status = "completed" if success else "failed"
                self._emit_model_download_event(model=model, status=status)
                return {"action": "download", "success": success}
        raise ValueError(f"Unbekannte Modellaktion: {action}")

    def get_plugin_overview(self) -> List[Dict[str, Any]]:
        if not self.plugin_manager:
            return []
        try:
            return self.plugin_manager.get_plugin_overview()
        except Exception as exc:
            self.logger.debug("Plugin-Übersicht nicht verfügbar: %s", exc)
            return []

    def _should_enable_web_ui(self) -> bool:
        """Prüft, ob Web UI aktiviert sein soll."""
        env_flag = os.getenv("JARVIS_WEB_UI", "").strip().lower()
        if env_flag in {"1", "true", "yes"}:
            return True
        try:
            web_cfg = self.settings.get("web_ui", {}) if self.settings else {}
            return bool(web_cfg.get("enabled", False))
        except Exception:
            return False

    def _start_web_ui_server(self) -> None:
        """Startet den FastAPI Web-Server in einem separaten Thread."""
        try:
            from api.jarvis_api import app, set_jarvis_instance
        except ImportError as e:
            self.logger.warning(f"Web UI konnte nicht geladen werden (api.jarvis_api nicht gefunden): {e}")
            return

        try:
            set_jarvis_instance(self)
            
            # Konfigurieren von uvicorn
            config = uvicorn.Config(
                app=app,
                host="0.0.0.0",
                port=8000,
                log_level="info",
                access_log=False,
                use_colors=False,
            )
            self._web_server = uvicorn.Server(config=config)
            
            # Starten in eigenem Thread
            self._web_ui_thread = threading.Thread(
                target=self._run_web_server,
                daemon=True,
                name="WebUI-Server"
            )
            self._web_ui_thread.start()
            
            self.logger.info("🌐 Web UI Server gestartet auf http://localhost:8000")
        except Exception as e:
            self.logger.warning(f"Web UI Server konnte nicht gestartet werden: {e}")

    def _run_web_server(self) -> None:
        """Führt den Web-Server aus (läuft in separatem Thread)."""
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._web_server.serve())
        except Exception as e:
            self.logger.warning(f"Web Server Fehler: {e}")

    def start(self):
        self.is_running = True
        self.logger.info("J.A.R.V.I.S. wird gestartet...")
        self._maybe_start_go_services()
        
        # Starte Web UI wenn aktiviert
        if self._should_enable_web_ui():
            self._start_web_ui_server()
        
        if self.remote_gateway:
            self.remote_gateway.mark_not_ready()
            self.remote_gateway.start()

        if self.settings.get('first_run', True):
            self.run_debug_mode()
            self.settings.set('first_run', False)

        self.start_listening()
        self.gui.update_status("Bereit")
        self.gui.run()

    def stop(self):
        self.is_running = False
        self.stop_listening()
        
        # Stoppe Web Server
        if self._web_server:
            try:
                self._web_server.should_exit = True
                self.logger.info("Web UI Server wird beendet")
            except Exception as e:
                self.logger.debug(f"Web Server konnte nicht gestoppt werden: {e}")
        
        try:
            if hasattr(self, "tts") and self.tts:
                self.tts.shutdown()
        except Exception:
            pass
        if self.plugin_manager:
            self.plugin_manager.shutdown()
        if hasattr(self, "update_scheduler") and self.update_scheduler:
            self.update_scheduler.stop()
        if self.remote_gateway:
            try:
                self.remote_gateway.stop()
            except Exception as exc:
                self.logger.debug("Remote-Gateway konnte nicht gestoppt werden: %s", exc)
        if self.web_interface:
            try:
                self.web_interface.stop()
            except Exception as exc:
                self.logger.debug("Web-Interface konnte nicht gestoppt werden: %s", exc)
        self.logger.info("J.A.R.V.I.S. wird beendet")
        self._stop_go_services()

    def run_debug_mode(self):
        self.logger.info("Debug-Modus: Systemprüfungen werden durchgeführt...")
        self.logger.info("Debug-Modus abgeschlossen")

    def on_wake_word_detected(self):
        if self.is_running:
            self.listening = True
            if getattr(self, "wake_word_enabled", True):
                try:
                    self.tts.speak("Ja, ich höre.")
                except Exception as exc:
                    self.logger.error(f"Akustische Rückmeldung fehlgeschlagen: {exc}")
                self.gui.update_status("Höre zu...")
                self.logger.info("Wake-Word erkannt")

    def on_command_recognized(self, command_text):
        if not self.is_running:
            return
        self.logger.info('Befehl erkannt: %s', command_text)
        self.gui.add_user_message(command_text)
        self.listening = False

    def start_listening(self) -> bool:
        recognizer = getattr(self, "speech_recognizer", None)
        if not recognizer:
            return False
        self.listening = True
        if getattr(self, "speech_thread", None) and self.speech_thread.is_alive():
            return True
        self.speech_thread = threading.Thread(target=recognizer.start_listening, daemon=True)
        self.speech_thread.start()
        return True

    def stop_listening(self) -> bool:
        self.listening = False
        recognizer = getattr(self, "speech_recognizer", None)
        if not recognizer:
            return False
        try:
            recognizer.stop_listening()
        except Exception as exc:
            self.logger.debug("Spracherkennung konnte nicht gestoppt werden: %s", exc)
            return False
        return True


def main():
    """Hauptfunktion"""
    try:
        os.makedirs("data", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        os.makedirs("models", exist_ok=True)
        from utils.logger import Logger
        Logger().set_level("DEBUG")
        print("Debug-Logs: logs/jarvis.log")

        try:
            settings_for_reporting = Settings()
            ErrorReporter(settings_for_reporting).install_global_hook()
        except Exception as _err:
            Logger().warning(f"Fehler-Reporter konnte nicht installiert werden: {_err}")

        jarvis = JarvisAssistant()
        jarvis.start()

    except KeyboardInterrupt:
        print("\nJ.A.R.V.I.S. wird beendet...")
    except Exception as e:
        print(f"Fehler beim Start: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()