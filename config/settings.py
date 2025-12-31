"""
Konfigurationsmodul für J.A.R.V.I.S.
Verwaltet Einstellungen und Konfigurationsdateien
"""

import json
import os
from pathlib import Path
from utils.logger import Logger

class Settings:
    """Verwaltet Anwendungseinstellungen"""
    
    def __init__(self):
        self.logger = Logger()
        self.config_file = Path("data/settings.json")
        self.default_settings = self.get_default_settings()
        
        self.settings = self.load_settings()
        self.logger.info("Einstellungen initialisiert")
    
    def _read_settings_file(self):
        """Liest die Settings-Datei und toleriert UTF-8 mit/ohne BOM."""
        last_error = None
        for encoding in ("utf-8-sig", "utf-8"):
            try:
                with open(self.config_file, "r", encoding=encoding) as handle:
                    return json.load(handle)
            except UnicodeError as err:
                last_error = err
            except json.JSONDecodeError as err:
                last_error = err
                break
        if last_error:
            raise last_error
        return {}


    def get_default_settings(self):
        """Gibt Standard-Einstellungen zurueck"""
        defaults = {
            # Allgemeine Einstellungen
            "first_run": True,
            "debug_mode": False,
            "auto_start": False,
            "theme": "dark",

            # Sprach-Einstellungen
            "speech": {
                "language": "de-DE",
                "wake_words": ["jarvis", "hey jarvis", "hallo jarvis"],
                "wake_word_enabled": True,
                "tts_rate": 180,
                "tts_volume": 0.8,
                "voice_id": None,
                "tts_backend": "pyttsx3",  # z.B. pyttsx3 | xtts | elevenlabs (zukuenftig)
                "tts_xtts_speaker": None,
                "voice_preset": "jarvis_marvel",  # Wunschstimme/Preset-Name
                "stream_tts": True,
                "min_command_words": 3,
                "whisper_model": "large-v3",
                "command_hotwords": [
                    "oeffne",
                    "starte",
                    "mach auf",
                    "beende",
                    "schliesse",
                    "stopp",
                    "spiele musik",
                    "lautstarke hoch",
                    "lautstarke runter",
                    "suche",
                    "zeige status"
                ],
                "command_synonyms": {
                    "open_program": ["oeffne", "offne", "mach auf", "starte", "programm starten"],
                    "close_program": ["schliesse", "mach zu", "beende", "programm schliessen"],
                    "knowledge_search": ["suche", "finde", "recherchiere", "was ist"],
                    "play_media": ["spiele musik", "musik abspielen", "spiel musik"],
                    "stop_media": ["stopp", "stoppe", "musik stoppen"],
                    "volume_up": ["lauter", "lautstarke hoch", "erhoehe lautstarke"],
                    "volume_down": ["leiser", "lautstarke runter", "senke lautstarke"],
                    "time_query": ["wie spaet", "uhrzeit", "wie viel uhr"],
                    "date_query": ["welches datum", "welcher tag"]
                },
                "preferred_programs": [],
                "recognition": {
                    "command_timeout": 1.7,
                    "silence_timeout": 0.7,
                    "max_command_duration": 3.8
                }
            },
            # STT-/Whisper-Konfiguration
            "stt": {
                "engine": "faster_whisper",
                "model": "Systran/faster-whisper-large-v3",
                "device": "cuda",
                "compute_type": "float16",
                "default_mode": "command",
                "mode_profiles": {
                    "command": {
                        "language": "de",
                        "beam_size": 1,
                        "temperature": 0.0,
                        "patience": None,
                        "vad_filter": True,
                        "vad_parameters": {
                            "threshold": 0.62,
                            "min_speech_duration_ms": 300,
                            "min_silence_duration_ms": 700,
                            "speech_pad_ms": 180,
                            "max_speech_duration_s": 4.0
                        },
                        "condition_on_previous_text": False,
                        "no_speech_threshold": 0.6,
                        "initial_prompt": "Deutschsprachige Kurzbefehle wie 'öffne', 'starte', 'lauter', 'leiser', 'stopp', 'abbrechen', 'zeige status', 'wie spät ist es', 'suche', 'spiele musik'."
                    },
                    "dictation": {
                        "language": "de",
                        "beam_size": 5,
                        "temperature": 0.0,
                        "patience": 0.0,
                        "vad_filter": True,
                        "vad_parameters": {
                            "threshold": 0.55,
                            "min_speech_duration_ms": 200,
                            "min_silence_duration_ms": 500,
                            "speech_pad_ms": 150
                        },
                        "condition_on_previous_text": True,
                        "no_speech_threshold": 0.55
                    }
                }
            },

            # Audio-Einstellungen
            "audio": {
                "sample_rate": 16000,
                "chunk_size": 8000,
                "channels": 1,
                # Eingabegeraet: Name oder Index (einer von beiden)
                "input_device": None,  # Name bevorzugt
                "input_device_index": None,
                "output_device": None,
                "output_device_index": None,
                "output_device_id": None
            },

            # Wissens-Einstellungen
            "knowledge": {
                "cache_duration_hours": 24,
                "max_cache_size": 1000,
                "enable_wikipedia": True,
                "enable_wikidata": False,
                "auto_cleanup": True,
                "expansion": {
                    "enabled": True,
                    "interval_minutes": 180,
                    "topics": [
                        "kuenstliche intelligenz",
                        "cybersecurity",
                        "nachhaltige energie",
                        "software engineering"
                    ]
                }
            },

            # System-Einstellungen
            "system": {
                "monitor_interval": 5,
                "max_log_size_mb": 10,
                "backup_count": 5,
                "enable_system_control": True
            },

            # Modell-Einstellungen
            "models": {
                "llm": {
                    "llama3": {
                        "load_strategy": "startup"
                    },
                    "mistral": {
                        "load_strategy": "on_demand"
                    },
                    "deepseek": {
                        "load_strategy": "on_demand"
                    }
                },
                "tts": {
                    "xtts": {
                        "load_strategy": "on_demand",
                        "enabled": True,
                        "default_speaker": "speaker_0",
                        "prompt_on_missing_speaker": True
                    }
                },
                "stt": {
                    "whisper": {
                        "load_strategy": "startup",
                        "enabled": True
                    }
                }
            },

            # Remote-Control / WebSocket
            "remote_control": {
                "enabled": False,
                "host": "127.0.0.1",
                "port": 8765,
                "token": "",
                "broadcast_conversation": True,
                "allow_status_queries": True,
                "command_timeout_seconds": 45.0
            },

            # Web-Interface
            "web_interface": {
                "enabled": True,
                "host": "127.0.0.1",
                "port": 5050,
                "token": "",
                "allow_guest_commands": False,
                "command_timeout_seconds": 45.0,
                "auto_open_browser": True,
                "allowed_ips": [],
                "rate_limit_window_seconds": 60,
                "rate_limit_max_requests": 120
            },
            "desktop_app": {
                "enabled": False,
                "window_title": "J.A.R.V.I.S.",
                "width": 1280,
                "height": 820,
                "frameless": False,
                "background_color": "#0b1220",
                "open_devtools": False,
                "suppress_browser": True
            },

            # Antwort-/Textlaengen-Einstellungen
            "response": {
                "condense_enabled": True,
                "min_chars": 220,
                "max_chars": 800
            },

            # NLU-/Kontext-Einstellungen
            "nlu": {
                "enable_slang_normalization": True,
                "ambiguity_threshold": 0.08
            },

            # Konversationskontext
            "context": {
                "enabled": True,
                "max_history": 20
            },

            # API-Einstellungen
            "apis": {
                "wikipedia_language": "de",
                "timeout_seconds": 10,
                "retry_attempts": 3,
                "enable_external_apis": True
            },

            # Telemetrie/Fehlerberichte
            "telemetry": {
                "error_reporting": {
                    "enabled": True,
                    "send_anonymous": False,
                    "max_reports_per_day": 25
                }
            }
        }
        defaults["security"] = self.get_default_security_settings()
        return defaults

    def get_default_security_settings(self):
        """Standard-Sicherheitsprofil fuer Lese-, Schreib- und Automationsrechte"""
        base_dir = Path.cwd()
        home_dir = Path.home()
        return {
            "encrypt_data": False,
            "log_conversations": True,
            "store_feedback": True,
            "privacy_mode": False,
            "audit_logging": True,
            "default_role": "user",
            "default_security_level": "normal",
            "auth": {
                "passphrase": None,
                "passphrase_hint": None,
                "vault_reference": "security_passphrase",
                "passphrase_cache_ttl": 600,
                "voice_match_threshold": 0.75,
            },
            "authenticator": {
                "required": True,
                "configured": False,
                "setup_pending": False,
                "issuer": "JarvisCore",
                "account_name": "JarvisCore-WebUI",
                "vault_reference": "security_totp_secret",
                "configured_at": None,
            },
            "read": {
                "allowed_directories": [
                    str(base_dir),
                    str(home_dir)
                ],
                "denied_directories": [
                    "C:/Windows",
                    "C:/Program Files",
                    "C:/Program Files (x86)"
                ],
                "max_file_size_mb": 8,
                "allow_system_info": True,
                "allow_process_listing": True,
                "allow_network_info": True,
                "allow_event_logs": False,
                "allow_window_introspection": True,
                "allow_screenshots": False
            },
            "write": {
                "allowed_directories": [
                    str(base_dir / "output"),
                    str(base_dir / "data")
                ],
                "denied_directories": [
                    "C:/Windows",
                    "C:/Program Files",
                    "C:/Program Files (x86)"
                ],
                "require_confirmation": True,
                "command_whitelist": {},
                "script_whitelist": []
            },
            "safe_mode": {
                "apply_changes": True,
                "notify_gui": True
            },
            "automation": {
                "allow_workflows": True,
                "max_steps": 10,
                "require_confirmation": True
            },
            "voice": {
                "profiles_required": True,
                "min_profiles": 1
            },
        }

    def load_settings(self):
        """Lädt Einstellungen aus Datei"""
        try:
            if self.config_file.exists():
                loaded_settings = self._read_settings_file()

                
                # Mit Default-Settings mergen
                merged_settings = self.merge_settings(self.default_settings, loaded_settings)
                
                self.logger.info("Einstellungen aus Datei geladen")
                return merged_settings
            else:
                self.logger.info("Keine Einstellungsdatei gefunden, verwende Standard-Einstellungen")
                self.save_settings(self.default_settings)
                return self.default_settings.copy()
                
        except Exception as e:
            self.logger.error(f"Fehler beim Laden der Einstellungen: {e}")
            return self.default_settings.copy()
    
    def merge_settings(self, default, loaded):
        """Merged geladene Einstellungen mit Standard-Einstellungen"""
        merged = default.copy()
        
        for key, value in loaded.items():
            if key in merged:
                if isinstance(value, dict) and isinstance(merged[key], dict):
                    merged[key] = self.merge_settings(merged[key], value)
                else:
                    merged[key] = value
            else:
                merged[key] = value
        
        return merged
    
    def save_settings(self, settings=None):
        """Speichert Einstellungen in Datei"""
        try:
            if settings is None:
                settings = self.settings
            
            # Verzeichnis erstellen falls nicht vorhanden
            self.config_file.parent.mkdir(exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            
            self.logger.info("Einstellungen gespeichert")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Speichern der Einstellungen: {e}")
            return False
    
    def get(self, key, default=None):
        """Gibt Einstellungswert zurück"""
        keys = key.split('.')
        value = self.settings
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key, value):
        """Setzt Einstellungswert"""
        keys = key.split('.')
        setting = self.settings
        
        try:
            # Zum letzten Schlüssel navigieren
            for k in keys[:-1]:
                if k not in setting:
                    setting[k] = {}
                setting = setting[k]
            
            # Wert setzen
            setting[keys[-1]] = value
            
            # Automatisch speichern
            self.save_settings()
            
            self.logger.info(f"Einstellung gesetzt: {key} = {value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Setzen der Einstellung {key}: {e}")
            return False
    
    def reset_to_defaults(self):
        """Setzt alle Einstellungen auf Standard zurück"""
        self.settings = self.default_settings.copy()
        self.save_settings()
        self.logger.info("Einstellungen auf Standard zurückgesetzt")
    
    def get_speech_settings(self):
        """Gibt Sprach-Einstellungen zurück"""
        return self.get('speech', {})
    
    def get_audio_settings(self):
        """Gibt Audio-Einstellungen zurück"""
        return self.get('audio', {})
    
    def get_knowledge_settings(self):
        """Gibt Wissens-Einstellungen zurück"""
        return self.get('knowledge', {})
    
    def get_system_settings(self):
        """Gibt System-Einstellungen zurück"""
        return self.get('system', {})
    
    def get_gui_settings(self):
        """Gibt GUI-Einstellungen zurück"""
        return self.get('gui', {})

    def get_model_settings(self, model_type=None):
        """Gibt Modelleinstellungen (optional nach Typ) zurueck"""
        models_cfg = self.get('models', {}) or {}
        if not isinstance(models_cfg, dict):
            return {}
        if model_type is None:
            return models_cfg
        section = models_cfg.get(model_type, {})
        return section if isinstance(section, dict) else {}

    def get_model_load_strategy(self, model_key, default='on_demand', model_type='llm'):
        """Liefert die konfigurierte Lade-Strategie fuer ein Modell"""
        section = self.get_model_settings(model_type)
        if not isinstance(section, dict):
            return default
        entry = section.get(model_key, {})
        strategy = entry.get('load_strategy') if isinstance(entry, dict) else None
        if strategy in ('startup', 'on_demand'):
            return strategy
        return default

    def set_model_load_strategy(self, model_key, strategy, model_type='llm'):
        """Speichert die Lade-Strategie fuer ein Modell"""
        if strategy not in ('startup', 'on_demand'):
            self.logger.warning(f"Ungueltige Modell-Strategie fuer {model_key}: {strategy}")
            return False
        models_cfg = self.get('models', {}) or {}
        if not isinstance(models_cfg, dict):
            models_cfg = {}
        section = models_cfg.get(model_type)
        if not isinstance(section, dict):
            section = {}
        entry = section.get(model_key)
        if not isinstance(entry, dict):
            entry = {}
        entry['load_strategy'] = strategy
        section[model_key] = entry
        models_cfg[model_type] = section
        self.set('models', models_cfg)
        return True

    def is_model_enabled(self, model_key, default=True, model_type='llm'):
        """Gibt zurueck, ob ein Modell aktiviert ist."""
        section = self.get_model_settings(model_type)
        if not isinstance(section, dict):
            return default
        entry = section.get(model_key)
        if isinstance(entry, dict) and 'enabled' in entry:
            return bool(entry.get('enabled'))
        return default

    def set_model_enabled(self, model_key, enabled, model_type='llm'):
        """Aktiviert/deaktiviert ein Modell."""
        models_cfg = self.get('models', {}) or {}
        if not isinstance(models_cfg, dict):
            models_cfg = {}
        section = models_cfg.get(model_type)
        if not isinstance(section, dict):
            section = {}
        entry = section.get(model_key)
        if not isinstance(entry, dict):
            entry = {}
        entry['enabled'] = bool(enabled)
        section[model_key] = entry
        models_cfg[model_type] = section
        self.set('models', models_cfg)
        return True
    
    def update_speech_settings(self, **kwargs):
        """Aktualisiert Sprach-Einstellungen"""
        current = self.get_speech_settings()
        if current is not None:
            current.update(kwargs)
            self.set('speech', current)
    
    def update_audio_settings(self, **kwargs):
        """Aktualisiert Audio-Einstellungen"""
        current = self.get_audio_settings()
        if current is not None:
            current.update(kwargs)
            self.set('audio', current)
    
    def export_settings(self, export_path):
        """Exportiert Einstellungen in Datei"""
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Einstellungen exportiert nach: {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Exportieren der Einstellungen: {e}")
            return False
    
    def import_settings(self, import_path):
        """Importiert Einstellungen aus Datei"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                imported_settings = json.load(f)
            
            # Validierung der importierten Einstellungen
            if self.validate_settings(imported_settings):
                self.settings = self.merge_settings(self.default_settings, imported_settings)
                self.save_settings()
                
                self.logger.info(f"Einstellungen importiert aus: {import_path}")
                return True
            else:
                self.logger.error("Importierte Einstellungen sind ungültig")
                return False
                
        except Exception as e:
            self.logger.error(f"Fehler beim Importieren der Einstellungen: {e}")
            return False
    
    def validate_settings(self, settings):
        """Validiert Einstellungen-Dictionary"""
        try:
            # Basis-Validierung
            if not isinstance(settings, dict):
                return False
            
            # Erforderliche Hauptkategorien prüfen
            required_categories = ['speech', 'audio', 'knowledge', 'system', 'web_interface']
            for category in required_categories:
                if category not in settings or not isinstance(settings[category], dict):
                    return False
            
            # Spezifische Validierungen
            speech = settings.get('speech', {})
            if 'tts_rate' in speech and not (50 <= speech['tts_rate'] <= 300):
                return False
            
            if 'tts_volume' in speech and not (0.0 <= speech['tts_volume'] <= 1.0):
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler bei Einstellungs-Validierung: {e}")
            return False
    
    def get_all_settings(self):
        """Gibt alle Einstellungen zurück"""
        return self.settings.copy()
    
    def has_setting(self, key):
        """Prüft ob Einstellung existiert"""
        return self.get(key) is not None






