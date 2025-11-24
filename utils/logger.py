"""
Logger-Modul für J.A.R.V.I.S.
Zentralisiertes Logging-System
"""

import logging
import logging.handlers
import os
import datetime
from pathlib import Path


class Logger:
    """Zentraler Logger für J.A.R.V.I.S."""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.setup_logging()
            Logger._initialized = True

    def setup_logging(self):
        """Konfiguriert das Logging-System"""
        # Log-Verzeichnis erstellen
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        # Log-Datei-Pfad
        log_file = log_dir / "jarvis.log"

        # Logger konfigurieren
        self.logger = logging.getLogger("J.A.R.V.I.S.")
        self.logger.setLevel(logging.INFO)

        # Formatter erstellen
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)

        # File Handler mit Rotation
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)

        # Handler hinzufügen (nur einmal)
        if not self.logger.handlers:
            self.logger.addHandler(console_handler)
            self.logger.addHandler(file_handler)

        # Erste Log-Nachricht
        self.logger.info("=== J.A.R.V.I.S. Logger initialisiert ===")

    def debug(self, msg, *args, **kwargs):
        """Debug-Nachricht loggen (kompatibel zur stdlib-Signatur)"""
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        """Info-Nachricht loggen (kompatibel zur stdlib-Signatur)"""
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        """Warning-Nachricht loggen (kompatibel zur stdlib-Signatur)"""
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        """Error-Nachricht loggen (kompatibel zur stdlib-Signatur)"""
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        """Critical-Nachricht loggen (kompatibel zur stdlib-Signatur)"""
        self.logger.critical(msg, *args, **kwargs)

    def log_exception(self, exception, context=""):
        """Exception mit Kontext loggen"""
        if context:
            self.logger.error(
                f"Exception in {context}: {str(exception)}", exc_info=True
            )
        else:
            self.logger.error(f"Exception: {str(exception)}", exc_info=True)

    def log_user_interaction(self, user_input, assistant_response):
        """Benutzer-Interaktion loggen"""
        self.logger.info(f"USER: {user_input}")
        self.logger.info(f"ASSISTANT: {assistant_response}")

    def log_system_action(self, action, result):
        """System-Aktion loggen"""
        self.logger.info(f"SYSTEM_ACTION: {action} - Result: {result}")

    def log_api_call(self, api_name, query, success):
        """API-Aufruf loggen"""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(
            f"API_CALL: {api_name} - Query: {query} - Status: {status}"
        )

    def log_speech_recognition(self, text, confidence=None):
        """Spracherkennung loggen"""
        if confidence:
            self.logger.info(f"SPEECH_RECOGNITION: '{text}' (Confidence: {confidence})")
        else:
            self.logger.info(f"SPEECH_RECOGNITION: '{text}'")

    def log_tts(self, text):
        """Text-to-Speech loggen"""
        self.logger.info(f"TTS: '{text}'")

    def log_knowledge_query(self, query, found):
        """Wissensabfrage loggen"""
        status = "FOUND" if found else "NOT_FOUND"
        self.logger.info(f"KNOWLEDGE_QUERY: '{query}' - Status: {status}")

    def set_level(self, level):
        """Log-Level setzen"""
        if isinstance(level, str):
            level = getattr(logging, level.upper(), logging.INFO)

        self.logger.setLevel(level)
        for handler in self.logger.handlers:
            if isinstance(handler, logging.FileHandler):
                handler.setLevel(logging.DEBUG)
            else:  # Console handler
                handler.setLevel(level)

    def get_log_stats(self):
        """Log-Statistiken abrufen"""
        try:
            log_file = Path("logs/jarvis.log")
            if not log_file.exists():
                return {"lines": 0, "size": 0, "last_modified": None}

            stat = log_file.stat()
            with open(log_file, "r", encoding="utf-8") as f:
                lines = sum(1 for _ in f)

            return {
                "lines": lines,
                "size": stat.st_size,
                "last_modified": datetime.datetime.fromtimestamp(stat.st_mtime),
            }

        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen der Log-Statistiken: {e}")
            return {"lines": 0, "size": 0, "last_modified": None}

    def clear_logs(self):
        """Löscht alle Log-Dateien"""
        try:
            log_dir = Path("logs")
            for log_file in log_dir.glob("*.log*"):
                log_file.unlink()

            # Logger neu initialisieren
            self.logger.handlers.clear()
            self.setup_logging()

            self.logger.info("Log-Dateien geleert")
            return True

        except Exception as e:
            self.logger.error(f"Fehler beim Löschen der Log-Dateien: {e}")
            return False

    def export_logs(self, export_path):
        """Exportiert Logs in Datei"""
        try:
            log_file = Path("logs/jarvis.log")
            if log_file.exists():
                import shutil

                shutil.copy2(log_file, export_path)

                self.logger.info(f"Logs exportiert nach: {export_path}")
                return True
            else:
                self.logger.warning("Keine Log-Datei zum Exportieren gefunden")
                return False

        except Exception as e:
            self.logger.error(f"Fehler beim Exportieren der Logs: {e}")
            return False

    def get_recent_logs(self, lines=100):
        """Gibt die letzten N Log-Zeilen zurück"""
        try:
            log_file = Path("logs/jarvis.log")
            if not log_file.exists():
                return []

            with open(log_file, "r", encoding="utf-8") as f:
                entries = f.readlines()
            return entries[-lines:]

        except Exception as e:
            self.logger.error(f"Fehler beim Lesen der Logs: {e}")
            return []


__all__ = ["Logger"]
