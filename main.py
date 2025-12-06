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
        """Initialisiert die Desktop- oder Web-UI (jetzt mit Dear ImGui)."""
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

        # Versuche Dear ImGui Desktop-App zu laden
        if self.desktop_app_enabled:
            try:
                from desktop.jarvis_imgui_app import create_jarvis_imgui_gui
                self.desktop_gui = create_jarvis_imgui_gui(self)
                self.logger.info("🎮 Dear ImGui Desktop-App geladen (GPU-beschleunigt)")
                return self.desktop_gui
            except ImportError as exc:
                self.logger.warning("Dear ImGui nicht verfügbar (%s), falle auf Web-Interface zurück", exc)
                self.logger.info("Installiere mit: pip install dearpygui")
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
        """Nicht mehr relevant für ImGui (kein Qt-Threading), aber behalten für Kompatibilität."""
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

    # ... (Rest der Methoden bleiben unverändert)
    # Gekürzt für Übersichtlichkeit - alle anderen Methoden bleiben identisch

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
