#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
J.A.R.V.I.S. - Deutscher KI-Sprachassistent
Hauptmodul fär den Start der Anwendung

Hinweis: Die Web-UI wurde entfernt. Nutze die Desktop-UI unter desktop/
"""

import sys
import os
import threading
import time
import json
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


class HeadlessGUI:
    """Minimal Ersatz-GUI für headless Betrieb (API-only)."""

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
        self._logger.info("┌─" * 40)
        self._logger.info("│ J.A.R.V.I.S. Core Backend gestartet")
        self._logger.info("│ Web-UI entfernt - nutze Desktop UI unter desktop/")
        self._logger.info("│ API: http://127.0.0.1:5050")
        self._logger.info("│ WebSocket: ws://127.0.0.1:8765")
        self._logger.info("│ Beenden: STRG+C")
        self._logger.info("└─" * 40)
        
        ready_cb = getattr(self._jarvis, "on_gui_ready", None)
        if callable(ready_cb):
            try:
                ready_cb()
            except Exception as exc:
                self._logger.debug("Remote-Ready Callback konnte nicht aufgerufen werden: %s", exc)
        
        while self._jarvis.is_running:
            time.sleep(0.5)


class JarvisAssistant:
    """Hauptklasse für den J.A.R.V.I.S. Assistenten (API-Only Modus)"""

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
        self._conversation_history: List[Dict[str, Any]] = []
        self.system_monitor = SystemMonitor(update_interval=2.0)
        self.speech_thread: Optional[threading.Thread] = None
        self._pending_authenticator_payload: Optional[Dict[str, str]] = None

        # Komponenten initialisieren
        self.plugin_manager = PluginManager(self.logger)
        self.knowledge_manager = KnowledgeManager()
        self.crawler_client = CrawlerClient()
        self.system_control = SystemControl(self.security_manager, self.settings)
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
                "Authenticator-App fehlt: Nutze die Desktop-UI für TOTP-Einrichtung."
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
            
        # Headless GUI (kein UI)
        self.gui = HeadlessGUI(self, self.logger)
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
            self.logger.warning(f"Autodiagnose konnte nicht ausgeführt werden: {exc}")

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

        self.logger.info("✅ J.A.R.V.I.S. Core Backend initialisiert (API-only)")

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
                "Remote-WebSocket aktiv (ws://%s:%s)",
                remote_cfg.get('host', '127.0.0.1'),
                remote_cfg.get('port', 8765),
            )
        except Exception as exc:
            self.logger.error(f"Remote-Control konnte nicht initialisiert werden: {exc}")
            self.remote_gateway = None

    def _publish_remote_event(self, event_type: str, payload: Optional[Dict[str, Any]] = None) -> None:
        target = getattr(self, "remote_gateway", None)
        if not target:
            return
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

    def on_gui_ready(self) -> None:
        """Wird aufgerufen sobald die API bereit ist."""
        if self.remote_gateway:
            self.remote_gateway.mark_ready()
        self._publish_remote_event("status", {"state": "ready"})

    def get_runtime_status(self) -> Dict[str, Any]:
        """Liefert kompakten Status für Remote-Anfragen."""
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

    def start(self):
        """Startet den Assistenten (API-Only)"""
        self.is_running = True
        self.logger.info("🚀 J.A.R.V.I.S. Core Backend wird gestartet...")
        
        if self.remote_gateway:
            self.remote_gateway.mark_not_ready()
            self.remote_gateway.start()

        # Debug-Modus bei erstem Start
        if self.settings.get('first_run', True):
            self.run_debug_mode()
            self.settings.set('first_run', False)

        # Spracherkennung aktivieren
        self.start_listening()

        self.gui.update_status("Bereit")

        # Headless loop
        self.gui.run()

    def stop(self):
        """Stoppt den Assistenten"""
        self.is_running = False
        self.stop_listening()
        
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
                
        self.logger.info("🛑 J.A.R.V.I.S. Core Backend wird beendet")

    # ... REST OF THE METHODS UNCHANGED ...
    # (Die restlichen Methoden bleiben identisch, wurden zur Kürze weggelassen)


def main():
    """Hauptfunktion"""
    try:
        os.makedirs("data", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        os.makedirs("models", exist_ok=True)
        
        from utils.logger import Logger
        Logger().set_level("DEBUG")
        print("┌─" * 40)
        print("│ J.A.R.V.I.S. Core Backend")
        print("│ Version: 2.0.0 (API-Only)")
        print("│ Web-UI entfernt - nutze Desktop UI")
        print("│ Debug-Logs: logs/jarvis.log")
        print("└─" * 40)

        try:
            settings_for_reporting = Settings()
            ErrorReporter(settings_for_reporting).install_global_hook()
        except Exception as _err:
            Logger().warning(f"Fehler-Reporter konnte nicht installiert werden: {_err}")

        jarvis = JarvisAssistant()
        jarvis.start()

    except KeyboardInterrupt:
        print("\n🛑 J.A.R.V.I.S. wird beendet...")
    except Exception as e:
        print(f"❌ Fehler beim Start: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
