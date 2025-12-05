"""

Befehlsverarbeitungsmodul fuer J.A.R.V.I.S.

Verarbeitet Sprachbefehle und koordiniert Antworten

"""



import json

import re

import datetime
import random
import difflib
import os
import requests

from pathlib import Path

from typing import Dict, Any, Optional, List, Tuple, Set, Sequence, Union

FILE_REFERENCE_EXTENSIONS = (
    'txt', 'md', 'rtf', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'csv', 'ppt', 'pptx',
    'json', 'xml', 'yaml', 'yml', 'ini', 'toml', 'cfg', 'log', 'html', 'htm', 'tex', 'odt', 'ods', 'odp',
    'py', 'pyw', 'pyi', 'js', 'jsx', 'ts', 'tsx', 'java', 'kt', 'kts', 'swift', 'cs', 'cpp', 'c', 'h', 'hpp',
    'go', 'rs', 'rb', 'php', 'sql', 'sh', 'bash', 'zsh', 'ps1', 'psm1', 'bat', 'cmd', 'css', 'scss', 'less',
    'vue', 'svelte'
)

FILE_REFERENCE_PATTERN = re.compile(
    r'(?P<file>(?:[A-Za-z]:[\/])?[\w .()\-\/]+\.(?:' + '|'.join(FILE_REFERENCE_EXTENSIONS) + r'))',
    re.IGNORECASE,
)

FILE_REFERENCE_PREFIXES = (
    'was steht in der datei',
    'was steht in der',
    'was steht in',
    'lies bitte',
    'lies die datei',
    'lese die datei',
    'lese den inhalt von',
    'lese den inhalt der',
    'zeige mir den inhalt von',
    'zeige mir den inhalt der',
    'zeig mir den inhalt von',
    'zeig mir den inhalt der',
    'inhalt von',
    'inhalt der',
    'oeffne die datei',
    'oeffne',
    'offne',
)

from utils.logger import Logger
from utils.secure_storage import CredentialStore, EphemeralSecret

from core.nlu.intent_engine import IntentEngine, IntentMatch
from core.nlu.normalizer import TextNormalizer
from core.preferences_manager import PreferencesManager
from core.adaptive_context_manager import AdaptiveContextManager
from core.media_router import MediaRouter
from core.hotword_manager import HotwordManager
from core.security_protocol import PriorityLevel

from config.persona import persona


class CommandServiceClient:
    """HTTP-Client fuer den Go-basierten commandd-Service."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        token: Optional[str] = None,
        *,
        timeout: float = 5.0,
        logger: Optional[Logger] = None,
    ) -> None:
        env_disable = os.getenv("JARVIS_COMMANDD_ENABLED")
        disable_flag = env_disable is not None and env_disable.strip().lower() in {"0", "false", "no"}
        chosen_url = base_url or os.getenv("JARVIS_COMMANDD_URL") or "http://127.0.0.1:7075"
        if disable_flag:
            chosen_url = ""
        self.base_url = chosen_url.rstrip("/") if chosen_url else ""
        self.token = token or os.getenv("JARVIS_COMMANDD_TOKEN") or os.getenv("COMMANDD_TOKEN")
        self.timeout = timeout
        self.enabled = bool(self.base_url)
        self.logger = logger or Logger()
        self.session = requests.Session()

    @classmethod
    def from_settings(cls, settings: Optional[Any] = None, logger: Optional[Logger] = None) -> "CommandServiceClient":
        base_url = None
        token = None
        timeout = 5.0
        try:
            raw_settings = getattr(settings, "settings", {}) if settings else {}
            go_cfg = raw_settings.get("go_services") or {}
            cmd_cfg = go_cfg.get("commandd", go_cfg) if isinstance(go_cfg, dict) else {}
            if isinstance(cmd_cfg, dict):
                base_url = cmd_cfg.get("base_url") or cmd_cfg.get("url")
                token = cmd_cfg.get("token") or cmd_cfg.get("api_key")
                timeout = float(cmd_cfg.get("timeout_seconds", timeout))
        except Exception:
            pass
        return cls(base_url=base_url, token=token, timeout=timeout, logger=logger)

    def execute(self, text: str, *, metadata: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        if not self.enabled:
            return None
        payload = {
            "text": text,
            "metadata": metadata or {},
            "context": context or {},
        }
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["X-API-Key"] = self.token
        try:
            resp = self.session.post(f"{self.base_url}/command/execute", json=payload, headers=headers, timeout=self.timeout)
            if not resp.ok:
                return None
            return resp.json()
        except Exception as exc:
            self.logger.debug("commandd execute fehlgeschlagen: %s", exc)
            return None



class CommandProcessor:

    """Verarbeitet und interpretiert Benutzerbefehle"""

    

    def __init__(
        self,
        knowledge_manager,
        system_control,
        tts,
        plugin_manager: Optional[Any] = None,
        learning_manager: Optional[Any] = None,
        voice_biometrics: Optional[Any] = None,
        *,
        task_core: Optional[Any] = None,
        reinforcement_core: Optional[Any] = None,
        security_protocol: Optional[Any] = None,
        llm_manager: Optional[Any] = None,
        settings: Optional[Any] = None,
    ):

        self.logger = Logger()
        self.system_control = system_control
        # Settings zuerst setzen, damit Clients sie sehen
        self.settings = settings or getattr(self.system_control, 'settings', None)
        self.commandd_client = CommandServiceClient.from_settings(settings=self.settings, logger=self.logger)

        self.knowledge_manager = knowledge_manager
        self.tts = tts
        self.plugin_manager = plugin_manager
        self.learning_manager = learning_manager
        self.voice_biometrics = voice_biometrics
        self.security_protocol = security_protocol
        self.task_core = task_core
        self.reinforcement_core = reinforcement_core

        # Settings Zugriff (ueber SystemControl bevorzugt, falls vorhanden)
        if getattr(self.system_control, 'settings', None) is not None:
            self.settings = getattr(self.system_control, 'settings', None)
        nlu_cfg = {}
        ctx_cfg = {}
        if self.settings is not None:
            try:
                nlu_cfg = self.settings.get('nlu', {}) or {}
                ctx_cfg = self.settings.get('context', {}) or {}
            except Exception:
                nlu_cfg, ctx_cfg = {}, {}

        # Umgangssprache/Slang Normalisierung
        self.enable_slang_norm = bool(nlu_cfg.get('enable_slang_normalization', True))
        self.normalizer = TextNormalizer() if self.enable_slang_norm else None
        self.ambiguity_threshold = float(nlu_cfg.get('ambiguity_threshold', 0.08))

        self.security_passphrase: Optional[str] = None
        self.passphrase_hint: Optional[str] = None
        self.voice_match_threshold: float = 0.75
        self._credential_store = CredentialStore()
        self._passphrase_secret = EphemeralSecret()
        self._passphrase_credential_id = "security_passphrase"
        if self.settings is not None:
            try:
                security_cfg = self.settings.get('security', {}) or {}
                auth_cfg = security_cfg.get('auth', {}) or {}
                vault_reference = str(auth_cfg.get('vault_reference') or 'security_passphrase')
                cache_ttl = int(auth_cfg.get('passphrase_cache_ttl', 600) or 600)
                self._passphrase_secret = EphemeralSecret(ttl_seconds=cache_ttl)
                self._passphrase_credential_id = vault_reference
                raw_passphrase = auth_cfg.get('passphrase')
                if isinstance(raw_passphrase, str) and raw_passphrase.strip():
                    secret_value = raw_passphrase.strip()
                    try:
                        self._credential_store.store_secret(self._passphrase_credential_id, secret_value)
                        auth_cfg['passphrase'] = None
                        security_cfg['auth'] = auth_cfg
                        self.settings.set('security', security_cfg)
                    except Exception as vault_err:
                        self.logger.error("Passphrase konnte nicht sicher gespeichert werden: %s", vault_err)
                        self._passphrase_secret.set(secret_value)
                    else:
                        self._passphrase_secret.set(secret_value)
                else:
                    stored_secret = self._credential_store.retrieve_secret(self._passphrase_credential_id)
                    if stored_secret:
                        self._passphrase_secret.set(stored_secret)
                hint = auth_cfg.get('passphrase_hint')
                if isinstance(hint, str) and hint.strip():
                    self.passphrase_hint = hint.strip()
                threshold = auth_cfg.get('voice_match_threshold')
                if threshold is not None:
                    self.voice_match_threshold = max(0.5, float(threshold))
            except Exception:
                pass
        if self.voice_biometrics and hasattr(self.voice_biometrics, 'threshold'):
            try:
                self.voice_biometrics.threshold = float(self.voice_match_threshold)
            except Exception:
                pass

        self.creator_triggers = [
            'wer hat dich erschaffen',
            'wer hat dich gebaut',
            'wer hat dich gemacht',
            'wer hat dich programmiert',
            'wer ist dein entwickler',
            'wer ist dein erschaffer',
            'wer ist dein ersteller',
            'wer hat dich erstellt',
            'wer ist dein creator',
            'wer ist dein erbauer',
            'wer hat jarvis erschaffen',
            'dein entwickler',
            'dein erschaffer',
        ]

        

        # LLM-Manager fuer erweiterte KI-Funktionen

        self.llm_manager = llm_manager
        if self.llm_manager is None:
            try:
                from core.llm_manager import LLMManager

                self.llm_manager = LLMManager(settings=self.settings)
                self.logger.info("LLM-Manager erfolgreich initialisiert")
            except Exception as e:
                self.logger.warning(f"LLM-Manager konnte nicht initialisiert werden: {e}")
                self.llm_manager = None

        

        # Kontextgrenze anwenden, falls konfiguriert
        self.max_history = int(ctx_cfg.get('max_history', 20)) if ctx_cfg else 20
        # Kontext-Manager
        self.ctx_manager = AdaptiveContextManager(
            enabled=bool((ctx_cfg or {}).get('enabled', True)),
            max_history=self.max_history,
            weighting=(ctx_cfg or {}).get('adaptive_weights'),
        )

        # Umlaute in normalisierte Form umwandeln
        self._normalize_trans = str.maketrans({
            '\u00e4': 'ae',  # a umlaut
            '\u00f6': 'oe',  # o umlaut
            '\u00fc': 'ue',  # u umlaut
            '\u00df': 'ss',  # sharp s
            '\u00c4': 'Ae',  # A umlaut
            '\u00d6': 'Oe',  # O umlaut
            '\u00dc': 'Ue',  # U umlaut
        })
        self.context = {

            'last_command': '',

            'last_topic': '',

            'conversation_history': [],

            'conversation_mode': 'standard',

            'voice_mode': 'neutral',

            'media_state': {},

            'logic_path': 'default',

            'adaptive_context': {},
            'pending_high_risk_authorization': None,
        }

        

        self.program_aliases = {

            'edge': ['edge', 'microsoft edge', 'msedge'],

            'browser': ['browser', 'internet', 'chrome', 'firefox', 'webbrowser'],

            'notepad': ['notepad', 'editor', 'texteditor', 'notizblock'],

            'vscode': ['visual studio code', 'vs code', 'vscode', 'code editor'],

            'calculator': ['rechner', 'taschenrechner', 'calculator', 'calc'],

            'cmd': ['cmd', 'eingabeaufforderung', 'kommandozeile', 'terminal'],

            'powershell': ['powershell', 'pwsh'],

            'explorer': ['explorer', 'datei explorer', 'dateimanager', 'ordner', 'dateien'],

            'paint': ['paint', 'mspaint', 'zeichenprogramm'],

            'word': ['word', 'microsoft word', 'winword', 'textverarbeitung'],

            'excel': ['excel', 'microsoft excel', 'tabellenkalkulation'],

            'powerpoint': ['powerpoint', 'microsoft powerpoint', 'praesentation'],

            'spotify': ['spotify', 'musikplayer', 'musik app'],

            'steam': ['steam']

        }

        self.program_display_names = {

            'edge': 'Microsoft Edge',

            'browser': 'Der Browser',

            'notepad': 'Notepad',

            'vscode': 'Visual Studio Code',

            'calculator': 'Der Rechner',

            'cmd': 'Die Eingabeaufforderung',

            'powershell': 'PowerShell',

            'explorer': 'Der Datei-Explorer',

            'paint': 'Paint',

            'word': 'Microsoft Word',

            'excel': 'Microsoft Excel',

            'powerpoint': 'Microsoft PowerPoint',

            'spotify': 'Spotify',

            'steam': 'Steam'

        }



        if hasattr(self.system_control, 'get_dynamic_program_displays'):

            for key, display in self.system_control.get_dynamic_program_displays().items():

                self.program_display_names.setdefault(key, display)

        if hasattr(self.system_control, 'get_dynamic_program_aliases'):

            for key, aliases in self.system_control.get_dynamic_program_aliases().items():

                bucket = self.program_aliases.setdefault(key, [])

                for alias in aliases:

                    if alias and alias not in bucket:

                        bucket.append(alias)

        self.hotword_manager: Optional[HotwordManager] = None
        self._intent_hint_config: Dict[str, Dict[str, object]] = {}
        self._intent_keyword_lookup: Dict[str, Tuple[str, float]] = {}
        self._filler_words: Set[str] = set()
        self._short_command_whitelist: Set[str] = set()
        self._music_stopwords: Set[str] = {
            'ist', 'ein', 'eine', 'einen', 'einem', 'einer', 'der', 'die', 'das', 'den', 'dem', 'des',
            'und', 'aber', 'mal', 'bitte', 'doch', 'jetzt', 'hier', 'da', 'nur', 'auch', 'noch',
            'nochmal', 'weiter', 'weiterhin', 'weitergehen', 'lass', 'uns', 'mich', 'mir', 'dir',
            'fuer', 'fuer', 'ab', 'auf', 'zu', 'zum', 'zur', 'vom', 'am', 'an', 'im', 'in', 'vom', 'mit', 'von',
            'youtube', 'musik', 'song', 'titel', 'video', 'playlist', 'abspielen', 'spielen',
            'spiel', 'spiele', 'spielen', 'mach', 'machen', 'bitte', 'den', 'die', 'das', 'dieses',
            'diesen', 'dieser', 'meine', 'meinen', 'mein', 'deine', 'dein', 'unsere', 'uns',
            'wiedergabe',
        }
        self.functional_intents: Set[str] = {
            'music_youtube',
            'open_program',
            'close_program',
            'create_file',
            'system_status',
            'time_query',
            'date_query',
            'help',
        }
        self.functional_intent_confidence = 0.55
        try:
            self.hotword_manager = HotwordManager(self.settings)
            self._intent_hint_config = self.hotword_manager.get_intent_hint_config()
            self._intent_keyword_lookup = self._build_intent_keyword_lookup()
            self._filler_words = self.hotword_manager.get_filler_words()
            self._short_command_whitelist = self.hotword_manager.get_short_command_whitelist()
            try:
                hotwords_snapshot = self.hotword_manager.get_hotwords()
            except Exception:
                hotwords_snapshot = []
            if hotwords_snapshot:
                self.context['command_hotwords'] = hotwords_snapshot
        except Exception as exc:
            self.logger.debug(f"Hotword-Manager konnte nicht initialisiert werden: {exc}")
            self.hotword_manager = None
            self._intent_hint_config = {}
            self._intent_keyword_lookup = {}
            self._filler_words = set()
            self._short_command_whitelist = set()

        try:
            self.media_router = MediaRouter(system_control=self.system_control, settings=self.settings)
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error(f"MediaRouter konnte nicht initialisiert werden: {exc}")
            self.media_router = None
        else:
            try:
                recent_state = self.media_router.refresh_state()
                if recent_state:
                    self._sync_media_state()
            except Exception as exc:
                self.logger.debug(f"MediaRouter-Status konnte nicht aktualisiert werden: {exc}")

        self._entertainment_material = {
            'smalltalk': [
                "Wussten Sie, dass Montag statistisch der produktivste Tag fuer neue Ideen ist? Welche Projekte stehen bei Ihnen gerade an?",
                "Ich habe noch im Kopf, dass wir kuerzlich ueber Ihre Automatisierungsplaene sprachen. Wie laeuft es damit?",
                "Wenn Sie eine kreative Pause brauchen: Viele erfolgreiche Teams planen bewusst Mini-Auszeiten ein. Sollen wir eine Inspiration organisieren?"
            ],
            'facts': [
                "Zufallsfakt: In Deutschland werden taeglich ueber 30 Millionen Tassen Kaffee getrunken.",
                "Tech-Fact: Der erste Computerbug wurde 1947 von Grace Hopper dokumentiert - es war tatsaechlich eine Motte in einem Relais.",
                "Produktivitaetsfakt: Der sogenannte Zeigarnik-Effekt besagt, dass angefangene Aufgaben leichter im Kopf bleiben als abgeschlossene."
            ],
            'jokes': [
                "Warum konnte der Entwickler nicht schlafen? Weil er noch einen offenen Thread hatte.",
                "Ich habe versucht, einen Witz ueber KI zu schreiben, aber er war einfach zu berechnet.",
                "Chef zum Admin: 'Warum ist der Server so langsam?' – Admin: 'Er hat noch Kaffeesatz im Cache.'"
            ],
            'prompts': [
                "Soll ich einen Zufallsfakt oder lieber einen Witz teilen?",
                "Wenn Sie Lust haben, kann ich nach aktuellen Schlagzeilen schauen oder eine kleine Geschichte erzaehlen.",
                "Ich habe ein paar inspirierende Ideen parat – einfach nach 'Zufallsfakt' oder 'Witz' fragen."
            ]
        }



        # Befehlsmuster laden

        self.load_command_patterns()

        

        try:

            self.intent_engine = IntentEngine(config_path=Path("config/intents.json"), logger=self.logger)

        except Exception as exc:

            self.logger.error(f"Intent engine initialisation failed: {exc}")

            self.intent_engine = IntentEngine(logger=self.logger)

        self.intent_handlers = {

            'greeting': self.handle_greeting,

            'goodbye': self.handle_goodbye,

            'system_status': self.handle_system_status,

            'open_program': self.handle_open_program,

            'close_program': self.handle_close_program,

            'create_file': self.handle_create_file,

            'knowledge_search': self.handle_knowledge_search,

            'time_query': self.handle_time_request,

            'date_query': self.handle_date_request,

            'help': self.handle_help,

            'creator_info': self.handle_creator_question,

            'personal_state': self.handle_personal_state,

            'ai_chat': self.handle_ai_chat,

            'entertainment_mode': self.handle_entertainment_mode,

            'neural_mode': self.handle_neural_mode,

            'music_youtube': self.handle_music_command,

            'emergency_mode': self.handle_emergency_mode,

        }

        self.context.setdefault('intent_history', [])



        self.logger.info("Befehlsprozessor initialisiert")

    

    def load_command_patterns(self):
        """
        Laedt Befehlsmuster aus JSON-Datei
        """
        try:
            commands_file = Path("data/commands.json")
            if commands_file.exists():
                with open(commands_file, 'r', encoding='utf-8') as f:
                    self.command_patterns = json.load(f)
            else:
                # Standard-Befehlsmuster erstellen
                self.create_default_commands()
            self.logger.info(f"Befehlsmuster geladen: {len(self.command_patterns)} Kategorien")
        except Exception as e:
            self.logger.error(f"Fehler beim Laden der Befehlsmuster: {e}")
            self.create_default_commands()

    

    def create_default_commands(self):
        """
        Erstellt Standard-Befehlsmuster
        """
        self.command_patterns = {

            "greeting": {

                "patterns": ["hallo", "guten morgen", "guten tag", "guten abend", "hi"],

                "responses": [

                    "Hallo! Wie kann ich Ihnen helfen?",

                    "Guten Tag! Was kann ich fuer Sie tun?",

                    "Hallo! Ich bin bereit fuer Ihre Befehle."

                ]

            },

            "system_status": {

                "patterns": ["systemstatus", "system status", "wie laeuft das system", "status"],

                "responses": ["Ich hole den Systemstatus fuer Sie."]

            },

            "open_program": {

                "patterns": ["oeffne", "starte", "programm starten", "application oeffnen"],

                "responses": ["Ich oeffne das Programm fuer Sie."]

            },

            "close_program": {

                "patterns": ["schliesse", "beende", "programm beenden"],

                "responses": ["Ich beende das Programm."]

            },

            "knowledge_search": {

                "patterns": ["suche", "finde", "informationen ueber", "was ist", "erklaere"],

                "responses": ["Ich suche nach Informationen fuer Sie."]

            },

            "time_date": {

                "patterns": ["wie spaet", "uhrzeit", "datum", "welcher tag"],

                "responses": ["Hier ist die aktuelle Zeit."]

            },

            "help": {

                "patterns": ["hilfe", "help", "was kannst du", "befehle"],
                "responses": ["Ich kann Ihnen bei verschiedenen Aufgaben helfen."]

            }

        }

        

        # Standard-Befehle speichern

        self.save_command_patterns()

    

    def save_command_patterns(self):

        """Speichert Befehlsmuster in JSON-Datei"""

        try:

            commands_file = Path("data/commands.json")

            with open(commands_file, 'w', encoding='utf-8') as f:

                json.dump(self.command_patterns, f, ensure_ascii=False, indent=2)

        except Exception as e:

            self.logger.error(f"Fehler beim Speichern der Befehlsmuster: {e}")

    def _refresh_adaptive_context(self) -> None:
        """Update adaptive context snapshot and chosen logic path."""
        manager = getattr(self, "ctx_manager", None)
        if not manager or not hasattr(manager, "snapshot"):
            return
        try:
            snapshot = manager.snapshot()
            self.context['adaptive_context'] = snapshot
            self.context['logic_path'] = manager.select_logic_path()
        except Exception as exc:
            self.logger.debug("Adaptive context refresh failed: %s", exc)

        security_mgr = getattr(getattr(self, 'security_protocol', None), 'security_manager', None)
        if security_mgr:
            try:
                security_mgr.update_access_context(
                    {
                        'logic_path': self.context.get('logic_path'),
                        'use_case': self.context.get('last_use_case'),
                        'priority': self.context.get('priority'),
                    }
                )
            except Exception:
                pass

    

    def process_command(self, command_text, metadata: Optional[Dict[str, Any]] = None):

        """Verarbeitet einen Befehl und gibt Antwort zurueck"""

        if not command_text or not command_text.strip():

            return "Entschuldigung, ich habe Sie nicht verstanden."

        meta = metadata or {}
        if meta:
            self.context['last_metadata'] = meta
            emotion = meta.get('emotion')
            if emotion:
                self.context['last_user_emotion'] = emotion
            speech_mode = meta.get('speech_mode')
            if speech_mode and self.context.get('conversation_mode') in (None, 'standard'):
                self._set_voice_mode(speech_mode)
            elif not speech_mode and self.context.get('conversation_mode') in (None, 'standard'):
                self._set_voice_mode('neutral')
        audio_blob = meta.get('audio_blob') if isinstance(meta, dict) else None
        requires_auth = False
        auth_result = {
            "required": False,
            "authorized": True,
            "score": None,
            "message": "Keine Authentifizierung erforderlich",
        }


        original_text = command_text

        normalized_text = command_text.strip()
        # Optional: Vorab an Go-Command-Router spiegeln (non-blocking)
        try:
            remote = self.commandd_client.execute(
                normalized_text,
                metadata=meta,
                context=self.context,
            )
            if remote and isinstance(remote, dict):
                remote_resp = remote.get("response")
                if isinstance(remote_resp, str) and remote_resp.strip():
                    return remote_resp
        except Exception:
            self.logger.debug("commandd Ausfuehrung fehlgeschlagen, nutze lokalen Pfad", exc_info=True)
        # Vor-Normalisierung: Slang/Umgangssprache reduzieren
        if self.normalizer is not None:
            try:
                normalized_text = self.normalizer.normalize(normalized_text)
            except Exception:
                pass

        # Einfache Pronomen-Aufloesung auf Basis des Kontexts
        try:
            resolved = self.ctx_manager.resolve_pronouns(normalized_text) if self.ctx_manager else normalized_text
        except Exception:
            resolved = normalized_text

        final_command = resolved

        final_lower = normalized_text.lower()

        if final_command.strip().isdigit() and not self.context.get('pending_clarification') and not self.context.get('pending_confirmation'):
            return 'Bitte formuliere den Befehl ausfuehrlicher als nur mit einer Zahl.'

        plugin_response: Optional[str] = None

        override_command: Optional[str] = None

        plugin_context_snapshot: Optional[Dict[str, Any]] = None

        intent_match: Optional[IntentMatch] = None

        if self.plugin_manager:

            plugin_response = self.plugin_manager.handle_user_message(normalized_text, self.context)

            plugin_context_snapshot = self.plugin_manager.get_context_snapshot()

            override_command = self.context.pop('override_command', None)



            if plugin_context_snapshot:

                self.context['plugin_context'] = plugin_context_snapshot

            else:

                self.context.pop('plugin_context', None)



            if override_command:

                final_command = override_command.strip() or normalized_text

                final_lower = final_command.lower()



        self.context['last_command'] = final_command

        feedback_reply = self._handle_feedback_if_any(final_command.lower(), final_command)
        if feedback_reply:
            self._record_assistant_message(feedback_reply, source='feedback')
            self._merge_learning_context()
            return feedback_reply
        if self._looks_like_incomplete_command(final_command):
            clarification = "Ich habe dich gehoert, aber der Befehl ist noch unvollstaendig. Kannst du ihn bitte konkretisieren?"
            self._record_assistant_message(clarification, source='clarify')
            self._merge_learning_context()
            return clarification
        # Turn im Kontext speichern
        try:
            self.ctx_manager.update_on_user(final_command, meta={"raw": original_text})
        except Exception:
            pass
        try:
            self.ctx_manager.observe(final_command, meta=meta, speaker="user")
        except Exception:
            pass
        self._refresh_adaptive_context()



        entry = {

            'timestamp': datetime.datetime.now().isoformat(),

            'user': final_command,

            'type': 'user_input',

        }

        if final_command != original_text:

            entry['raw'] = original_text

        self.context['conversation_history'].append(entry)

        if self._matches_creator_question(final_lower):

            response = self.handle_creator_question()

            self._record_assistant_message(response, source='system')

            return response



        if self.llm_manager:

            use_case_info = self.llm_manager.predict_use_case(final_command)

            self.context['last_use_case'] = use_case_info.get('use_case')

            self.context['use_case_scores'] = use_case_info.get('scores')



        if plugin_response:

            requires_auth_local = self._requires_voice_auth(final_lower, intent_match)
            auth_result_local = {
                "required": requires_auth_local,
                "authorized": True,
                "score": None,
                "message": "Keine Authentifizierung erforderlich",
            }
            if requires_auth_local:
                auth_result_local = self._verify_voice(audio_blob)
                if not auth_result_local.get('authorized'):
                    failure_message = auth_result_local.get('message') or 'Sicherheitspruefung fehlgeschlagen.'
                    self.context['command_map'] = self._build_command_map(
                        original_text,
                        final_command,
                        intent_match,
                        plugin_response,
                        failure_message,
                        requires_auth_local,
                        auth_result_local,
                        meta,
                    )
                    self._merge_learning_context()
                    return failure_message

            self.context['conversation_history'].append({

                'timestamp': datetime.datetime.now().isoformat(),

                'assistant': plugin_response,

                'type': 'assistant_response',

                'source': 'plugin'

            })

            if len(self.context['conversation_history']) > self.max_history:

                self.context['conversation_history'] = self.context['conversation_history'][-self.max_history:]

            if self.plugin_manager:

                self.plugin_manager.handle_assistant_message(plugin_response, self.context)

            self.context['command_map'] = self._build_command_map(
                original_text,
                final_command,
                intent_match,
                plugin_response,
                plugin_response,
                requires_auth_local,
                auth_result_local,
                meta,
            )
            self._merge_learning_context()
            return plugin_response



        task_response = self._handle_autonomous_request(final_command, final_lower, meta)
        if task_response:
            self._record_assistant_message(task_response, source='autonomous')
            self._merge_learning_context()
            return task_response

        response: Optional[str] = None



        normalized_for_engine = self._normalize_user_text(final_command)
        hint_info = self._collect_intent_hints(normalized_for_engine)
        engine_input = hint_info.get("engine_input", normalized_for_engine)
        bias_map: Dict[str, float] = hint_info.get("bias", {}) if isinstance(hint_info, dict) else {}
        if hint_info:
            self.context['intent_hints'] = hint_info

        if self.intent_engine:
            top_matches: List[IntentMatch] = []
            try:
                top_matches = self.intent_engine.rank(engine_input, limit=2)
            except Exception:
                top_matches = []

            if top_matches:
                if self.learning_manager:
                    for match in top_matches:
                        bias = self.learning_manager.get_intent_bias(match.name)
                        match.confidence = max(0.0, min(0.99, match.confidence + bias))
                    top_matches.sort(key=lambda entry: entry.confidence, reverse=True)
                if bias_map:
                    for match in top_matches:
                        boost = bias_map.get(match.name)
                        if boost:
                            match.confidence = max(0.0, min(0.99, match.confidence + boost))
                    top_matches.sort(key=lambda entry: entry.confidence, reverse=True)
                intent_match = top_matches[0]
                if intent_match.name in self.functional_intents and intent_match.confidence < self.functional_intent_confidence:
                    self.logger.debug(
                        "Intent '%s' unter Schwelle %.2f (%.3f) - behandel als unklar",
                        intent_match.name,
                        self.functional_intent_confidence,
                        intent_match.confidence,
                    )
                    intent_match = None
                    top_matches = []

                if len(top_matches) > 1:
                    diff = abs(top_matches[0].confidence - top_matches[1].confidence)
                    skip_clarification = (
                        intent_match.name in self.functional_intents
                        and intent_match.confidence >= self.functional_intent_confidence
                    )
                    # Häufiger Sonderfall: Begrüßung vs. persönlicher Zustand -> kein Nachfragen, nimm Top-Match
                    pair = {top_matches[0].name, top_matches[1].name}
                    if pair == {"greeting", "personal_state"}:
                        skip_clarification = True
                    if diff < self.ambiguity_threshold and not skip_clarification:
                        a = top_matches[0].name
                        b = top_matches[1].name
                        clarification = f"Meinten Sie '{a}' oder '{b}'? Bitte spezifizieren."
                        self._record_assistant_message(clarification, source='clarify')
                        self.context['clarification_ack'] = 'Verstanden.'
                        self.context['pending_clarification'] = {'options': [a, b], 'raw': final_command}
                        return clarification

        if not plugin_response:

            file_response = self._try_handle_file_request(final_command, intent_match)

            if file_response:

                return file_response

        if self.voice_biometrics:
            requires_auth = self._requires_voice_auth(final_lower, intent_match)
            passphrase_ok = bool(meta.get('passphrase_ok'))
            if requires_auth:
                auth_result = self._verify_voice(audio_blob)
                high_risk = requires_auth
                if passphrase_ok and high_risk:
                    auth_result['authorized'] = True
                    auth_result['message'] = 'Passphrase akzeptiert'
                if auth_result.get('authorized'):
                    if self.context.get('pending_high_risk_authorization'):
                        self.context['pending_high_risk_authorization'] = None
                else:
                    if high_risk and self._has_passphrase() and not passphrase_ok:
                        existing = self.context.get('pending_high_risk_authorization') or {}
                        attempts = int(existing.get('attempts', 0)) + 1
                        self.context['pending_high_risk_authorization'] = {
                            'command': final_command,
                            'original_text': original_text,
                            'intent': intent_match.name if intent_match else None,
                            'metadata': dict(meta),
                            'created_at': datetime.datetime.utcnow().isoformat(),
                            'attempts': attempts,
                            'hint': self.passphrase_hint,
                        }
                        prompt = 'Sicherheitsbestaetigung noetig. Sage deine Passphrase oder tippe sie ein.'
                        self._record_assistant_message(prompt, source='security')
                        self._merge_learning_context()
                        return prompt
                    failure_message = auth_result.get('message') or 'Sicherheitspruefung fehlgeschlagen.'
                    self.context['command_map'] = self._build_command_map(
                        original_text,
                        final_command,
                        intent_match,
                        plugin_response,
                        failure_message,
                        requires_auth,
                        auth_result,
                        meta,
                    )
                    self._merge_learning_context()
                    return failure_message
            else:
                auth_result['required'] = False
        else:
            requires_auth = False
            auth_result['required'] = False

        if intent_match:

            intent_match.raw_text = final_command

            intent_match.normalized_text = normalized_for_engine

            self.context['last_intent'] = intent_match.name

            history = self.context.setdefault('intent_history', [])

            history.append({

                'timestamp': datetime.datetime.now().isoformat(),

                'intent': intent_match.name,

                'confidence': round(intent_match.confidence, 3),

                'entities': intent_match.entities,

            })

            self.context['intent_history'] = history[-self.max_history:]

            # Kontext mit Intent/Entities aktualisieren
            try:
                self.ctx_manager.update_from_intent(intent_match.name, intent_match.entities, text=final_command)
            except Exception:
                pass
            try:
                self.ctx_manager.observe(final_command, meta=meta, speaker="user", intent=intent_match.name)
            except Exception:
                pass
            self._refresh_adaptive_context()

            # Gewohnheitslernen: Nutzung pro Intent zaehlen
            try:
                self.prefs.inc_usage(f"intent:{intent_match.name}")
            except Exception:
                pass
            if self.learning_manager:
                self.learning_manager.record_usage(intent_match.name, final_command)

            response = self._execute_intent(intent_match, final_command)
            if response and intent_match.name in self.functional_intents:
                self.context['skip_llm_fallback'] = True



        if not response:

            response = self.handle_unknown_command(final_command)

            intent_match = None



        clarification_ack = self.context.pop('clarification_ack', None)

        if clarification_ack:

            response = f"{clarification_ack}\n{response}"



        source = f"intent:{intent_match.name}" if intent_match else 'assistant'

        self._record_assistant_message(response, source=source)

        self.context['command_map'] = self._build_command_map(
            original_text,
            final_command,
            intent_match,
            plugin_response,
            response,
            requires_auth,
            auth_result,
            meta,
        )

        if self.plugin_manager:

            self.plugin_manager.handle_assistant_message(response, self.context)

            plugin_context_snapshot = self.plugin_manager.get_context_snapshot()

            if plugin_context_snapshot:

                self.context['plugin_context'] = plugin_context_snapshot

            else:

                self.context.pop('plugin_context', None)

        if self.learning_manager:
            if intent_match:
                failure_phrases = (
                    'nicht verstanden',
                    'konnte nicht',
                    'fehler',
                    'nicht gefunden',
                    'fehlgeschlagen',
                )
                success = True
                if isinstance(response, str):
                    lowered_resp = response.lower()
                    if any(phrase in lowered_resp for phrase in failure_phrases):
                        success = False
                self.learning_manager.record_outcome(intent_match.name, success)
            self._merge_learning_context()

        self.context.pop('skip_llm_fallback', None)

        return response



    def _execute_intent(self, match: IntentMatch, original_text: str) -> Optional[str]:

        handler = self.intent_handlers.get(match.name)

        if not handler and match.handler:

            handler = getattr(self, match.handler, None)

        if not handler:

            self.logger.debug(f"No handler registered for intent {match.name}")

            return None

        try:

            return handler(original_text, match)

        except TypeError:

            return handler(original_text)

        except Exception as exc:

            self.logger.error(f"Intent handler '{match.name}' failed: {exc}")

            return None



    def _build_intent_keyword_lookup(self) -> Dict[str, Tuple[str, float]]:
        lookup: Dict[str, Tuple[str, float]] = {}
        for intent, config in (self._intent_hint_config or {}).items():
            keywords = config.get('keywords') if isinstance(config, dict) else None
            boost = float(config.get('boost', 0.0)) if isinstance(config, dict) else 0.0
            if not keywords:
                continue
            for keyword in keywords:
                key = (keyword or '').strip()
                if not key:
                    continue
                lookup[key] = (intent, boost)
        return lookup

    def _resolve_program_key(self, text: str, match: Optional[IntentMatch]) -> Optional[str]:

        candidates: List[str] = []

        if match:

            for key in ('program', 'program_den'):

                value = match.entities.get(key) if match.entities else None

                if value:

                    candidates.append(value)

        if text:

            candidates.append(text)

        for candidate in candidates:

            resolved = self._find_program_candidate(candidate)

            if resolved:

                return resolved
        return None



    def _find_program_candidate(self, source: str) -> Optional[str]:
        if not source:
            return None
        cleaned = self._strip_command_fillers(source)
        text_lower = cleaned.lower().strip()
        if not text_lower:
            return None

        # 1) exakte Uebereinstimmung
        for program, aliases in self.program_aliases.items():
            if text_lower == program:
                return program
            if any(text_lower == alias for alias in aliases):
                return program

        # 2) Teilstring-Suche
        for program, aliases in self.program_aliases.items():
            if program in text_lower:
                return program
            if any(alias in text_lower for alias in aliases):
                return program

        # 3) Fuzzy Matching als letzte Stufe (z.B. "notpad" -> "notepad")
        try:
            name_to_program: Dict[str, str] = {}
            all_names: List[str] = []
            for prog, aliases in self.program_aliases.items():
                name_to_program[prog] = prog
                all_names.append(prog)
                for alias in aliases:
                    if alias:
                        normal_alias = alias.lower().strip()
                        name_to_program[normal_alias] = prog
                        all_names.append(normal_alias)
            match = difflib.get_close_matches(text_lower, all_names, n=1, cutoff=0.8)
            if match:
                resolved = name_to_program.get(match[0])
                if resolved:
                    return resolved
        except Exception:
            pass
        return None


    def _strip_command_fillers(self, text: str) -> str:
        if not text:
            return ""
        lowered = text.lower().strip()
        words = lowered.split()
        result: List[str] = []
        skipping = True
        for word in words:
            if skipping and word in self._filler_words:
                continue
            if skipping and word in {"programm", "program", "app", "anwendung"}:
                continue
            skipping = False
            result.append(word)
        return " ".join(result) if result else lowered


    def _locate_program_keyword(self, text: str) -> Optional[str]:
        if not text:
            return None
        for program, aliases in self.program_aliases.items():
            if not aliases:
                continue
            for alias in aliases:
                alias_norm = self._normalize_user_text(alias).lower()
                if not alias_norm:
                    continue
                if alias_norm in text:
                    return program
                if HotwordManager.approximate_contains(text, alias_norm, cutoff=0.9):
                    return program
        return None


    def _extract_file_reference(self, text: str) -> Optional[str]:

        if not text:

            return None

        match = FILE_REFERENCE_PATTERN.search(text)

        if not match:

            return None

        candidate = (match.group('file') or '').strip()

        normalized = candidate.replace('\\', '/')

        end_pos = len(normalized)

        start_pos = end_pos

        seen_separator = False

        allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-()')

        while start_pos > 0:

            ch = normalized[start_pos - 1]

            if ch == '/':

                seen_separator = True

                start_pos -= 1

                continue

            if ch == ' ':

                if not seen_separator:

                    break

                start_pos -= 1

                continue

            if ch == ':':

                start_pos -= 1

                continue

            if ch in allowed_chars:

                start_pos -= 1

                continue

            break

        normalized = normalized[start_pos:]

        normalized = normalized.strip("\"'")

        normalized = normalized.replace('\\', '/')

        if not normalized:

            return None

        normalized = re.sub(r'^localwissen/+', '', normalized, flags=re.IGNORECASE)

        normalized = re.sub(r'^[a-z]:/', '', normalized, flags=re.IGNORECASE)

        normalized = normalized.lstrip('./')

        normalized = normalized.strip()

        if not normalized:

            return None

        parts = [part for part in normalized.split('/') if part]

        if not parts:

            return None

        if len(parts) >= 2:

            candidate_norm = '/'.join(parts[-2:])

        else:

            candidate_norm = parts[-1]

        return candidate_norm

    @staticmethod
    def _strip_code_fences(block: Any) -> str:
        if not isinstance(block, str):
            return ""
        text = block.strip()
        if not text:
            return ""
        if text.startswith("```"):
            text = text[3:]
            newline = text.find("\n")
            if newline != -1:
                text = text[newline + 1:]
            if text.endswith("```"):
                text = text[:-3]
            return text.strip("\r\n")
        if text.startswith("'''") and text.endswith("'''") and len(text) >= 6:
            return text[3:-3].strip("\r\n")
        if text.startswith('"""') and text.endswith('"""') and len(text) >= 6:
            return text[3:-3].strip("\r\n")
        if len(text) >= 2 and ((text[0] == text[-1] == '"') or (text[0] == text[-1] == "'")):
            return text[1:-1]
        return text

    @staticmethod
    def _detect_overwrite_request(text: str) -> bool:
        lowered = (text or "").lower()
        keywords = (
            "ueberschreib",
            "ueberschreibe",
            "ueberschreiben",
            "overwrite",
            "override",
            "ersetze",
            "ersetzen",
            "ersetz",
            "neu schreiben",
            "neu erstellen",
        )
        return any(keyword in lowered for keyword in keywords)

    def _clean_content_segment(self, segment: str, *, before: bool = False) -> Tuple[str, bool]:
        if not segment:
            return "", False
        working = segment.strip()
        if not working:
            return "", False
        original = working
        if before:
            working = re.sub(r'(?:in|auf)\s+(?:die|den|das)?\s*(?:datei|file)\s*$', '', working, flags=re.IGNORECASE).strip()
        else:
            working = working.lstrip(':=- \t\r\n')
        leading_pattern = re.compile(
            r'^(?:und|mit|mit dem|mit der|mit den|mit folgendem|mit folgender|mit folgendes|und zwar|schreibe|schreib|speichere|fuege|setze|lege|packe|bitte)\s+',
            re.IGNORECASE,
        )
        working = leading_pattern.sub('', working, count=1)
        descriptor_pattern = re.compile(
            r'^(?:den|dem|die|das)?\s*(?:folgenden|folgender|folgendes)?\s*(?:inhalt|text|code|content|quellcode)\s*(?:code|text|inhalt|content)?\s*(?:von\s+)?',
            re.IGNORECASE,
        )
        working = descriptor_pattern.sub('', working, count=1)
        working = working.lstrip(':=- \t\r\n')
        cleaned = working.strip()
        if not cleaned:
            return "", bool(original)
        return cleaned, False

    def _extract_file_write_content(
        self,
        command: str,
        path: str,
        entities: Optional[Dict[str, Any]],
    ) -> Tuple[str, bool]:
        if isinstance(entities, dict):
            for key in ('content', 'code', 'text', 'inhalt', 'body'):
                value = entities.get(key)
                if value is not None:
                    text_value = str(value)
                    if text_value.strip():
                        return text_value, False
        command_text = command or ""
        normalized_path = path or ""
        variations = [
            normalized_path,
            normalized_path.replace('/', '\\'),
            normalized_path.replace('\\', '/'),
        ]
        lower_command = command_text.lower()
        before = command_text
        after = ""
        for candidate in dict.fromkeys(variations):
            if not candidate:
                continue
            lowered_candidate = candidate.lower()
            idx = lower_command.find(lowered_candidate)
            if idx != -1:
                before = command_text[:idx]
                after = command_text[idx + len(candidate):]
                break
        content_after, missing_after = self._clean_content_segment(after)
        if content_after:
            return content_after, False
        missing_flag = missing_after
        content_before, missing_before = self._clean_content_segment(before, before=True)
        if content_before:
            return content_before, False
        missing_flag = missing_flag or missing_before
        return "", missing_flag

    def _infer_creation_target(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        if not text:
            return None, None
        normalized = self._normalize_user_text(text) if hasattr(self, '_normalize_user_text') else text
        normalized_lower = (normalized or '').lower()
        if not normalized_lower:
            return None, None
        tokens = re.findall(r'[a-z0-9_]+', normalized_lower)
        if not tokens:
            return None, None
        base_dir: Optional[Path] = None
        location_hint: Optional[str] = None
        try:
            home = Path.home()
        except Exception:
            home = Path.cwd()
        if 'desktop' in normalized_lower or 'schreibtisch' in normalized_lower:
            base_dir = home / 'Desktop'
            location_hint = 'Desktop'
        elif 'dokumente' in normalized_lower or 'documents' in normalized_lower:
            base_dir = home / 'Documents'
            location_hint = 'Documents'
        elif 'downloads' in normalized_lower:
            base_dir = home / 'Downloads'
            location_hint = 'Downloads'
        elif 'musik' in normalized_lower or 'music' in normalized_lower:
            base_dir = home / 'Music'
            location_hint = 'Music'
        stopwords = {
            'ein', 'eine', 'einen', 'auf', 'in', 'im', 'ins', 'am', 'an', 'dem', 'den', 'der', 'die', 'das', 'zu',
            'zum', 'zur', 'mit', 'mein', 'meine', 'meinem', 'meinen', 'meiner', 'dein', 'deine', 'dessen', 'deren',
            'dieses', 'dieser', 'diesem', 'dies', 'das', 'ist', 'sei', 'sein', 'soll', 'sollte', 'bitte', 'py',
            'python', 'programm', 'program', 'skript', 'script', 'code', 'projekt', 'erstelle', 'erstellt',
            'erstellen', 'bau', 'baue', 'bauen', 'mach', 'mache', 'machen', 'desktop', 'schreibtisch',
            'dokumente', 'documents', 'downloads', 'music', 'musik'
        }
        stem: Optional[str] = None
        for idx, token in enumerate(tokens):
            if token in {'ein', 'eine', 'einen'}:
                collected: List[str] = []
                for next_token in tokens[idx + 1:]:
                    if next_token in stopwords:
                        if collected:
                            break
                        continue
                    collected.append(next_token)
                if collected:
                    stem = '-'.join(collected)
        if not stem:
            for token in reversed(tokens):
                if token not in stopwords:
                    stem = token
                    break
        if not stem:
            return None, location_hint
        safe_stem = re.sub(r'[^a-z0-9_-]+', '-', stem).strip('-_')
        if not safe_stem:
            return None, location_hint
        extension_map = [
            ('.py', {'python', 'py'}),
            ('.js', {'javascript', 'js'}),
            ('.ts', {'typescript', 'ts'}),
            ('.html', {'html'}),
            ('.css', {'css'}),
            ('.json', {'json'}),
            ('.ps1', {'powershell', 'ps', 'ps1'}),
            ('.bat', {'batch', 'bat', 'cmd'}),
            ('.sh', {'bash', 'shell', 'sh'}),
            ('.md', {'markdown', 'notiz', 'notizen'}),
        ]
        extension = '.txt'
        for candidate_ext, keywords in extension_map:
            if any(keyword in tokens for keyword in keywords):
                extension = candidate_ext
                break
        if safe_stem.endswith(extension):
            filename = safe_stem
        else:
            filename = f"{safe_stem}{extension}"
        try:
            if base_dir:
                full_path = base_dir / filename
            else:
                full_path = Path(filename)
        except Exception:
            return filename, location_hint
        return str(full_path), location_hint

    @staticmethod
    def _looks_like_plain_language(text: str) -> bool:
        stripped = (text or "").strip()
        if not stripped:
            return True
        code_markers = ("def ", "class ", "import ", "return ", "print(", " = ", "\n")
        if any(marker in stripped for marker in code_markers):
            return False
        letters = sum(1 for ch in stripped if ch.isalpha())
        ratio = letters / max(len(stripped), 1)
        if ratio < 0.6:
            return False
        words = stripped.split()
        if len(words) <= 4:
            return False
        return True

    @staticmethod
    def _template_taschenrechner() -> str:
        return """#!/usr/bin/env python3
\"\"\"Ein einfacher Konsolen-Taschenrechner.\"\"\"

import operator


OPS = {
    '+': operator.add,
    '-': operator.sub,
    '*': operator.mul,
    '/': operator.truediv,
}


def calc(a: float, op: str, b: float) -> float:
    if op not in OPS:
        raise ValueError(f\"Unbekannter Operator {op!r}\")
    if op == '/' and b == 0:
        raise ZeroDivisionError(\"Division durch Null ist nicht erlaubt\")
    return OPS[op](a, b)


def main() -> None:
    print(\"*** Taschenrechner ***\")
    print(\"Unterstuetzte Operatoren: +  -  *  /\")
    print(\"Beispiel: 5 * 3\\n\")
    history = []
    while True:
        raw = input(\"Eingabe (oder 'exit'): \").strip()
        if not raw:
            continue
        if raw.lower() in {\"exit\", \"quit\", \"ende\"}:
            break
        try:
            left, op, right = raw.split()
            result = calc(float(left), op, float(right))
            history.append(f\"{left} {op} {right} = {result}\")
            print(f\"= {result}\")
        except ValueError as err:
            print(f\"Fehler: {err}\")
        except ZeroDivisionError as err:
            print(f\"Fehler: {err}\")
    if history:
        print(\"\\nVerlauf:\")
        for entry in history:
            print(\"  \", entry)
    print(\"Auf Wiedersehen!\")


if __name__ == \"__main__\":
    main()
"""

    def _generate_content_from_description(self, description: str) -> Tuple[Optional[str], Optional[str]]:
        if not description:
            return None, None
        lowered = description.lower()
        tokens = re.findall(r"[a-zäöüß]+", lowered)
        norm_tokens = [token.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss") for token in tokens]
        keyword_factories = {
            "taschenrechner": (self._template_taschenrechner, "ein Python-Taschenrechner-Skript"),
            "calculator": (self._template_taschenrechner, "ein Python-Taschenrechner-Skript"),
        }
        for token in norm_tokens:
            for keyword, (factory, note) in keyword_factories.items():
                if keyword in token:
                    return factory(), note
                try:
                    ratio = difflib.SequenceMatcher(None, token, keyword).ratio()
                except Exception:
                    ratio = 0.0
                if ratio >= 0.78:
                    return factory(), note
        return None, None

    @staticmethod
    def _should_use_last_file(text: str) -> bool:
        lowered = (text or "").lower()
        triggers = (
            "oeffne die datei",
            "offne die datei",
            "mach die datei auf",
            "oeffne sie",
            "offne sie",
            "oeffne die letzte datei",
        )
        return any(trigger in lowered for trigger in triggers)


    def _fetch_file_content_by_reference(self, reference: str) -> Optional[str]:

        if not self.knowledge_manager:

            return None

        reference = (reference or '').strip()

        if not reference:

            return None

        normalized = reference.replace('\\', '/').strip()

        if not normalized:

            return None

        normalized_lower = normalized.lower()

        candidates = [normalized_lower]

        if not normalized_lower.startswith('localwissen::'):

            candidates.append(f'localwissen::{normalized_lower}')

        basename = normalized_lower.split('/')[-1]

        if basename and basename not in candidates:

            candidates.append(basename)

        if '/' not in normalized_lower:

            desktop_variant = f'desktop/{normalized_lower}'

            if desktop_variant not in candidates:

                candidates.append(desktop_variant)

            lw_desktop = f'localwissen::desktop/{normalized_lower}'

            if lw_desktop not in candidates:

                candidates.append(lw_desktop)

        if basename and not basename.startswith('localwissen::'):

            lw_basename = f'localwissen::{basename}'

            if lw_basename not in candidates:

                candidates.append(lw_basename)

        for candidate in candidates:

            key = (candidate or '').strip()

            if not key:

                continue

            try:

                result = self.knowledge_manager.search_knowledge(key)

            except Exception as exc:

                self.logger.error(f"File lookup failed for {key}: {exc}")

                continue

            if result:

                return result.strip()

        return None


    def _extract_document_path(self, content: str) -> Optional[str]:

        if not content:

            return None

        for line in content.splitlines():

            if line.lower().startswith('datei:'):

                return line.split(':', 1)[1].strip() or None

        return None


    def _resolve_file_on_disk(self, reference: str, content: Optional[str]) -> Optional[Path]:

        candidates: List[Path] = []

        ref = (reference or '').strip()

        if ref:

            ref_path = Path(ref)

            if ref_path.is_file():

                candidates.append(ref_path)

        normalized = ref.replace('\\', '/').strip(' ./')

        if normalized:

            if normalized.lower().startswith('localwissen::'):

                normalized_rel = normalized.split('::', 1)[1]

            else:

                normalized_rel = normalized

            candidates.extend(self._local_knowledge_candidates(normalized_rel))

        doc_path = self._extract_document_path(content or '')

        if doc_path:

            candidates.extend(self._local_knowledge_candidates(doc_path))

        visited = set()

        for candidate in candidates:

            if not candidate:

                continue

            key = str(candidate).lower()

            if key in visited:

                continue

            visited.add(key)

            try:

                if candidate.is_file():

                    return candidate

            except OSError:

                continue

        basename = Path(normalized or '').name

        local_root = self._local_knowledge_root()

        if basename and local_root and local_root.exists():

            try:

                for match in local_root.rglob(basename):

                    if match.is_file():

                        return match

            except Exception:

                pass

        return None


    def _local_knowledge_candidates(self, relative: str) -> List[Path]:

        local_root = self._local_knowledge_root()

        if not local_root:

            return []

        relative_clean = (relative or '').replace('\\', '/').strip('/')

        if not relative_clean:

            return []

        candidate = local_root.joinpath(*relative_clean.split('/'))

        alternates = [candidate]

        if candidate.exists():

            return alternates

        lower_candidate = local_root.joinpath(*[part.lower() for part in relative_clean.split('/')])

        if lower_candidate not in alternates:

            alternates.append(lower_candidate)

        return alternates


    def _local_knowledge_root(self) -> Optional[Path]:

        if self.knowledge_manager and hasattr(self.knowledge_manager, 'get_local_knowledge_path'):

            return self.knowledge_manager.get_local_knowledge_path()

        try:

            return Path.cwd() / 'LocalWissen'

        except Exception:

            return None


    def _wants_file_open(self, text: str, match: Optional[IntentMatch]) -> bool:

        raw_text = text or ''

        lowered = raw_text.lower()

        normalized = self._normalize_user_text(raw_text) if hasattr(self, '_normalize_user_text') else raw_text

        normalized_lower = (normalized or '').lower()

        search_space = lowered + ' ' + normalized_lower

        open_keywords = (
            'oeffne', 'offne', 'oeffnen', 'datei oeffnen', 'datei offnen', 'open', 'mach auf', 'mach die datei auf'
        )

        if any(keyword in search_space for keyword in open_keywords):

            return True

        if 'mach' in lowered and 'datei' in lowered and 'auf' in lowered:

            return True

        if match and getattr(match, 'name', '') == 'open_program':

            return True

        return False


    def _try_handle_file_request(self, text: str, match: Optional[IntentMatch]) -> Optional[str]:

        candidate = self._extract_file_reference(text)

        if not candidate and match and getattr(match, 'entities', None):

            for value in match.entities.values():

                maybe = self._extract_file_reference(str(value))

                if maybe:

                    candidate = maybe

                    break

        if not candidate:

            last_recent = self.context.get('last_created_file')

            if last_recent and self._should_use_last_file(text):

                if self.system_control and self.system_control.open_file_or_folder(str(last_recent)):

                    display_name = Path(str(last_recent)).name

                    return f"{display_name} wurde geoeffnet."

                return f"Ich konnte {last_recent} nicht oeffnen."

            return None

        wants_open = self._wants_file_open(text, match)

        content = self._fetch_file_content_by_reference(candidate)

        open_message = None

        file_path_for_open: Optional[Path] = None

        if wants_open:

            file_path_for_open = self._resolve_file_on_disk(candidate, content)

            if file_path_for_open and self.system_control and self.system_control.open_file_or_folder(str(file_path_for_open)):

                display_name = file_path_for_open.name

                open_message = f"{display_name} wurde geoeffnet."

        if content:

            content_stripped = content.strip()

            if open_message:

                return f"{open_message}\n\n{content_stripped}"

            return content_stripped

        if wants_open and not open_message:

            fallback_path = self._resolve_file_on_disk(candidate, None)

            if fallback_path and self.system_control and self.system_control.open_file_or_folder(str(fallback_path)):

                display_name = fallback_path.name

                return f"{display_name} wurde geoeffnet."

        return open_message


    def _extract_search_query(self, text: str) -> Optional[str]:
        if not text:
            return None
        base_text = text.strip()

        if base_text:

            simplified_for_files = base_text

            for prefix in FILE_REFERENCE_PREFIXES:

                simplified_for_files = re.sub(

                    rf'^\s*{re.escape(prefix)}\s+',

                    '',

                    simplified_for_files,

                    flags=re.IGNORECASE,

                )

            for candidate_text in (simplified_for_files.strip(), base_text):

                if not candidate_text:

                    continue

                file_reference = self._extract_file_reference(candidate_text)

                if file_reference:

                    return file_reference

        lowered = text.lower()

        cleaned = text

        triggers = (

            'suche nach', 'suche', 'finde', 'recherchiere', 'zeige mir',

            'was ist', 'erklaere', 'infos ueber', 'informationen ueber',

            'informationen zu', 'infos zu'

        )

        for trigger in triggers:

            if trigger in lowered:

                index = lowered.find(trigger)

                cleaned = cleaned[index + len(trigger):]

                lowered = lowered[index + len(trigger):]

        cleaned = cleaned.strip(' ?!.')

        cleaned = re.sub(r'^((nach|ueber|zu|von)\s+)+', '', cleaned, flags=re.IGNORECASE)

        cleaned = re.sub(r'^(?:den|der|die|das)?\s*(?:inhalt|datei|file|ordner)\s+', '', cleaned, flags=re.IGNORECASE)

        cleaned = cleaned.strip()

        return cleaned or None






    def classify_command(self, command_text):

        """Backward compatible helper that delegates to the intent engine."""

        if not command_text:

            return 'unknown'

        if self.intent_engine:

            match = self.intent_engine.match(command_text)

            if match:

                return match.name

        return 'unknown'

    

    def execute_command(self, command_type, original_text):

        """Legacy execution helper for backwards compatibility."""

        try:

            if self.intent_engine:

                match = self.intent_engine.match(original_text)

                if match and match.name == command_type:

                    result = self._execute_intent(match, original_text)

                    if result:

                        return result

            handler = self.intent_handlers.get(command_type)

            if handler:

                try:

                    return handler(original_text)

                except TypeError:

                    return handler(original_text, None)

            return self.handle_unknown_command(original_text)

        except Exception as exc:

            self.logger.error(f"Fehler bei Befehlsausfuehrung: {exc}")

            return "Entschuldigung, bei der Ausfuehrung des Befehls ist ein Fehler aufgetreten."

    

    def handle_creator_question(self, text: str = '', match: Optional[IntentMatch] = None) -> str:

        """Antwortet auf Fragen nach dem Erbauer."""

        statement = (

            f"Ich wurde von {self.creator_name} entwickelt. "

            f"{self.creator_name} hat mich aufgebaut, um auf diesem System zu helfen."

        )

        try:

            self.knowledge_manager.cache_knowledge("jarvis creator", statement, "System")

        except Exception:

            pass

        return statement



    def _matches_creator_question(self, text: str) -> bool:

        if not text:

            return False

        lowered = text.lower()
        return any(trigger in lowered for trigger in self.creator_triggers)



    def _record_assistant_message(self, message: str, source: str = "assistant") -> None:

        entry = {

            "timestamp": datetime.datetime.now().isoformat(),
            "assistant": message,
            "type": "assistant_response",
            "source": source

        }

        self.context.setdefault("conversation_history", []).append(entry)

        if len(self.context["conversation_history"]) > self.max_history:

            self.context["conversation_history"] = self.context["conversation_history"][-self.max_history:]

        # Kontext-Manager ueber Assistant-Turn informieren
        try:
            self.ctx_manager.update_on_assistant(message, meta={"source": source})
        except Exception:
            pass
        try:
            self.ctx_manager.observe(message, meta={"source": source}, speaker="assistant")
        except Exception:
            pass
        self._refresh_adaptive_context()

    def _handle_feedback_if_any(self, lowered_text: str, original_text: str) -> Optional[str]:
        text = (lowered_text or '').strip()
        if not text or not self.learning_manager:
            return None
        last_intent = self._get_last_intent()
        if text.startswith('korrektur:'):
            correction = original_text.split(':', 1)[1].strip() if ':' in original_text else ''
            entry = self.learning_manager.record_feedback(-1.0, original_text, correction=correction, intent=last_intent)
            self._propagate_feedback(entry)
            return 'Danke fuer die Korrektur. Ich passe die Antwort entsprechend an.'
        negative_triggers = (
            'das war falsch',
            'stimmt nicht',
            'das stimmt nicht',
            'falsch',
            'nicht richtig',
            'funktioniert nicht',
            'hat nicht geklappt',
        )
        positive_triggers = (
            'gut gemacht',
            'hat geklappt',
            'perfekt',
            'super',
            'toll',
            'richtig danke',
        )
        if any(trigger in text for trigger in negative_triggers):
            entry = self.learning_manager.record_feedback(-1.0, original_text, intent=last_intent)
            self._propagate_feedback(entry)
            return 'Alles klar, ich lerne daraus und verbessere die Antwort.'
        if any(trigger in text for trigger in positive_triggers):
            entry = self.learning_manager.record_feedback(+1.0, original_text, intent=last_intent)
            self._propagate_feedback(entry)
            return 'Freut mich, dass es passt. Ich merke mir das fuer zukuenftige Antworten.'
        return None

    def _propagate_feedback(self, entry: Optional[Dict[str, Any]]) -> None:
        if not entry:
            return
        reinforcement = None
        if getattr(self, 'reinforcement_core', None):
            try:
                reinforcement = self.reinforcement_core.register_feedback(entry)
            except Exception:
                reinforcement = None
        ctx = self.context.setdefault('reinforcement', {})
        if reinforcement:
            ctx['latest'] = reinforcement
            ctx['weights'] = getattr(self.reinforcement_core, 'latest_weights', {}).copy()
        else:
            ctx.setdefault('latest', entry)
            ctx.setdefault('weights', getattr(self.reinforcement_core, 'latest_weights', {}).copy())

    def _handle_autonomous_request(
        self, command_text: str, lowered: str, metadata: Dict[str, Any]
    ) -> Optional[str]:
        task_core = getattr(self, 'task_core', None)
        if not task_core:
            return None

        plan_triggers = ("plane ", "erstelle einen plan", "autonome aufgabe", "autonom")
        execute_triggers = ("fuehre den plan", "führe den plan", "starte den plan", "arbeite den plan ab")

        if any(trigger in lowered for trigger in plan_triggers):
            plan = task_core.create_plan(
                command_text,
                context={
                    'use_case': self.context.get('last_use_case'),
                    'logic_path': self.context.get('logic_path'),
                    'user_emotion': metadata.get('emotion'),
                },
            )
            self.context['task_plan'] = plan.to_dict()
            return task_core.render_plan(plan)

        if any(trigger in lowered for trigger in execute_triggers):
            active_plan = getattr(task_core, 'active_plan', None)
            if not active_plan:
                return 'Es liegt kein aktiver Aufgabenplan vor. Bitte zuerst einen Plan erstellen.'
            result = task_core.execute_plan(active_plan)
            self.context['task_result'] = result.to_dict()
            return task_core.render_execution(result)
        return None

    def _get_last_intent(self) -> Optional[str]:
        history = self.context.get('intent_history') or []
        if history:
            last_entry = history[-1]
            if isinstance(last_entry, dict):
                return last_entry.get('intent')
        return self.context.get('last_intent')

    def _requires_voice_auth(self, lowered_text: str, intent_match: Optional[IntentMatch]) -> bool:
        if not self.voice_biometrics:
            return False
        sensitive_keywords = (
            'loesch', 'loesche', 'delete', 'format', 'notfall', 'notruf', 'emergency',
            'alarm', 'sperr den pc', 'shutdown', 'herunterfahren', 'restart',
            'neu starten', 'netzwerk trennen'
        )
        if any(keyword in lowered_text for keyword in sensitive_keywords):
            return True
        if intent_match and intent_match.name == 'voice_enroll':
            return False
        if intent_match and intent_match.name in {'emergency_mode'}:
            return True
        return False

    def has_passphrase(self) -> bool:
        return self._has_passphrase()

    def validate_passphrase(self, candidate: str) -> bool:
        if not isinstance(candidate, str):
            return False
        secret_bytes = self._get_passphrase_bytes()
    def _has_passphrase(self) -> bool:
        if self._passphrase_secret.borrow_bytes():
            return True
        try:
            return self._credential_store.has_secret(self._passphrase_credential_id)
        except Exception:
            return False

    def _get_passphrase_bytes(self) -> Optional[bytes]:
        secret = self._passphrase_secret.borrow_bytes()
        if secret:
            return secret
        try:
            stored_secret = self._credential_store.retrieve_secret(self._passphrase_credential_id)
        except Exception as exc:
            self.logger.error("Passphrase konnte nicht gelesen werden: %s", exc)
            return None
        if stored_secret:
            self._passphrase_secret.set(stored_secret)
            return self._passphrase_secret.borrow_bytes()
        return None

    @staticmethod
    def _zeroize_buffer(buffer: bytearray) -> None:
        for idx in range(len(buffer)):
            buffer[idx] = 0
        if not secret_bytes:
            return False
        candidate_norm = bytearray(candidate.strip().lower().encode('utf-8'))
        secret_norm = bytearray(secret_bytes.decode('utf-8').strip().lower().encode('utf-8'))
        try:
            is_valid = secrets.compare_digest(secret_norm, candidate_norm)
        finally:
            self._zeroize_buffer(candidate_norm)
            self._zeroize_buffer(secret_norm)
        if is_valid:
            self._passphrase_secret.touch()
        return is_valid

    def _verify_voice(self, audio_blob: Optional[bytes]) -> Dict[str, Optional[float]]:
        result = {
            "required": True,
            "authorized": False,
            "score": None,
            "message": "Keine Sprachprobe vorhanden",
        }
        if not self.voice_biometrics:
            result["authorized"] = True
            result["message"] = "Keine Biometrie aktiviert"
            return result
        if not audio_blob:
            return result
        try:
            authorized, score = self.voice_biometrics.verify(audio_blob)
        except Exception as exc:
            self.logger.warning(f"Stimmverifikation fehlgeschlagen: {exc}")
            result["message"] = "Fehler bei der Stimmpruefung"
            return result
        result["authorized"] = bool(authorized)
        result["score"] = float(score) if score is not None else None
        result["message"] = "Stimme erkannt" if authorized else "Stimme nicht erkannt"
        return result

    def _build_command_map(
        self,
        original_text: str,
        final_command: str,
        intent_match: Optional[IntentMatch],
        plugin_response: Optional[str],
        response: Optional[str],
        requires_auth: bool,
        auth_result: Dict[str, Optional[float]],
        metadata: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        intent_data: Optional[Dict[str, Any]] = None
        if intent_match:
            intent_data = {
                "name": intent_match.name,
                "confidence": round(float(intent_match.confidence), 3),
                "entities": intent_match.entities or {},
            }
        voice_info = {
            "required": requires_auth,
            "authorized": bool(auth_result.get("authorized")),
            "score": auth_result.get("score"),
            "message": auth_result.get("message"),
        }
        preview = None
        if isinstance(response, str):
            preview = response if len(response) <= 200 else response[:200] + "..."
        safe_metadata: Dict[str, Any] = {}
        if isinstance(metadata, dict):
            for key, value in metadata.items():
                if key == 'audio_blob':
                    if value is None:
                        safe_metadata[key] = None
                    else:
                        safe_metadata[key] = f'<audio {len(value)} bytes>'
                else:
                    safe_metadata[key] = value
        return {
            "timestamp": datetime.datetime.now().isoformat(),
            "original_text": original_text,
            "processed_text": final_command,
            "intent": intent_data,
            "plugin_response": bool(plugin_response),
            "response_preview": preview,
            "voice_auth": voice_info,
            "metadata": safe_metadata,
        }

    def _merge_learning_context(self) -> None:
        if not self.learning_manager:
            return
        snapshot = self.learning_manager.get_snapshot()
        self.context['learning_summary'] = snapshot
        plugin_ctx = self.context.get('plugin_context')
        if not isinstance(plugin_ctx, dict):
            plugin_ctx = {}
        plugin_ctx['learning'] = snapshot
        command_map = self.context.get('command_map')
        if command_map:
            plugin_ctx['command_map'] = command_map
        self.context['plugin_context'] = plugin_ctx

    def _run_neural_synthesis(self, query: str) -> Optional[str]:
        """Fuehrt eine Neural-Mode-Recherche durch und formatiert die Antwort."""
        if not query or not self.knowledge_manager:
            return None
        try:
            synthesis = self.knowledge_manager.neural_synthesis(query)
        except Exception as exc:
            self.logger.error(f"Neural-Synthese fehlgeschlagen: {exc}")
            return None
        if not synthesis:
            return None
        summary = (synthesis.get('summary') or '').strip()
        sources = synthesis.get('sources') or []
        self.context['neural_last_sources'] = sources
        lines: List[str] = []
        if summary:
            lines.append(summary)
        if sources:
            lines.append('')
            lines.append('Quellenmix:')
            for idx, entry in enumerate(sources, 1):
                label = entry.get('label') or entry.get('source') or f'Quelle {idx}'
                highlight = (entry.get('highlight') or '').strip()
                if highlight and len(highlight) > 450:
                    highlight = highlight[:447] + '…'
                if highlight:
                    lines.append(f"{idx}. {label} – {highlight}")
                else:
                    lines.append(f"{idx}. {label}")
        response = '\n'.join([segment for segment in lines if segment is not None]).strip()
        return response or summary or None

    def _set_conversation_mode(self, mode: Optional[str]) -> None:
        if not mode or mode == 'standard':
            self.context['conversation_mode'] = 'standard'
            self._set_voice_mode('neutral')
            return
        self.context['conversation_mode'] = mode

    def _set_voice_mode(self, mode: Optional[str]) -> None:
        if not mode:
            self.context['voice_mode'] = 'neutral'
            return
        self.context['voice_mode'] = mode



    def handle_greeting(self, text: str = '', match: Optional[IntentMatch] = None):

        """Begruesst den Nutzer kontextsensitiv."""
        prompt = (
            "Erzeuge eine kurze (1-2 Saetze) Begruessung fuer den Nutzer. "
            "Sei sachlich und direkt hilfsbereit, keine Floskeln oder Erinnerungen. "
            f"Benutzereingabe: '{text}'. "
            "Enthalte einen Vorschlag, wie du helfen kannst (z.B. 'Wobei soll ich starten?')."
        )
        if self.llm_manager:
            try:
                llm_reply = self.llm_manager.generate_response(
                    prompt,
                    max_tokens=64,
                    use_case="conversation",
                )
                if llm_reply:
                    return llm_reply
            except Exception:
                pass
        # Fallback nur wenn LLM nicht verfuegbar
        current_hour = datetime.datetime.now().hour
        greeting = 'Guten Morgen' if 5 <= current_hour < 12 else ('Guten Tag' if current_hour < 18 else 'Guten Abend')
        return f"{greeting}! Wie kann ich Sie unterstuetzen?"


    def handle_personal_state(self, text: str = '', match: Optional[IntentMatch] = None):

        """Reagiert auf Fragen nach dem Befinden."""
        prompt = (
            "Beantworte eine Rueckfrage nach deinem Befinden kurz (1-2 Saetze), "
            "sachlich und service-orientiert. Keine ausschweifenden Floskeln, "
            "fuehre direkt zu einer Hilfsfrage. "
            f"Benutzereingabe: '{text}'."
        )
        if self.llm_manager:
            try:
                llm_reply = self.llm_manager.generate_response(
                    prompt,
                    max_tokens=64,
                    use_case="conversation",
                )
                if llm_reply:
                    return llm_reply
            except Exception:
                pass
        return 'Alles gut und einsatzbereit. Was soll ich fuer Sie tun?'

    def handle_entertainment_mode(self, text: str = '', match: Optional[IntentMatch] = None) -> str:
        """Aktiviert oder nutzt den Unterhaltungsmodus."""
        lowered = (text or '').lower()
        if any(keyword in lowered for keyword in ('beende', 'stop', 'genug', 'zurueck', 'raus aus')):
            self._set_conversation_mode('standard')
            self._set_voice_mode('neutral')
            self.context.pop('entertainment_last_type', None)
            return 'Unterhaltungsmodus beendet. Wir konzentrieren uns wieder auf Ihre Aufgaben.'

        repeat_request = any(trigger in lowered for trigger in ('noch einen', 'nochmal', 'weiter', 'mehr'))
        requested_type = None
        if any(word in lowered for word in ('witz', 'joke', 'lachen')):
            requested_type = 'jokes'
        elif any(word in lowered for word in ('zufallsfakt', 'fact', 'trivia', 'fakt')):
            requested_type = 'facts'
        elif any(word in lowered for word in ('news', 'nachrichten', 'tages', 'aktuell', 'heute')):
            requested_type = 'news'
        elif any(word in lowered for word in ('smalltalk', 'plauder', 'erzaeh', 'erzaehl', 'geschichte')):
            requested_type = 'smalltalk'
        elif repeat_request:
            requested_type = self.context.get('entertainment_last_type', 'smalltalk')

        self._set_conversation_mode('entertainment')
        self._set_voice_mode('humorvoll')

        if requested_type == 'news':
            try:
                news = self.knowledge_manager.search_external_sources("Aktuelle Nachrichten Deutschland heute")
            except Exception as exc:
                self.logger.error(f"News-Abruf fehlgeschlagen: {exc}")
                news = None
            if news:
                self.context['entertainment_last_type'] = 'news'
                return news
            requested_type = 'facts'

        if requested_type == 'jokes':
            selection = random.choice(self._entertainment_material['jokes'])
            self.context['entertainment_last_type'] = 'jokes'
            return selection

        if requested_type == 'facts':
            selection = random.choice(self._entertainment_material['facts'])
            self.context['entertainment_last_type'] = 'facts'
            return selection

        previous_topics = []
        plugin_context = self.context.get('plugin_context')
        if isinstance(plugin_context, dict):
            memory_ctx = plugin_context.get('memory') or {}
            if isinstance(memory_ctx, dict):
                previous_topics = list(memory_ctx.get('active_topics') or [])
        if not previous_topics and self.plugin_manager:
            try:
                for plugin_wrapper in getattr(self.plugin_manager, 'plugins', []):
                    if getattr(plugin_wrapper, 'plugin_name', '') == 'memory':
                        memory_plugin = getattr(plugin_wrapper, '_plugin', None)
                        manager = getattr(memory_plugin, 'memory_manager', None)
                        if manager and getattr(manager, 'active_topics', None):
                            previous_topics = list(manager.active_topics)
                            break
            except Exception:
                previous_topics = []

        if requested_type == 'smalltalk':
            base = random.choice(self._entertainment_material['smalltalk'])
        else:
            base = random.choice(self._entertainment_material['prompts'])

        if previous_topics:
            topic_snippet = ', '.join(previous_topics[:3])
            base += f" Uebrigens erinnere ich mich noch an unsere Themen rund um {topic_snippet}."

        self.context['entertainment_last_type'] = requested_type or 'smalltalk'
        return base

    def handle_neural_mode(self, text: str = '', match: Optional[IntentMatch] = None) -> str:
        """Schaltet den Neural Mode um und liefert bei Bedarf sofort eine Synthese."""
        lowered = (text or '').lower()
        exit_triggers = (
            'beende', 'stop', 'zurueck', 'standard', 'normalmodus', 'standardmodus',
            'deaktivier', 'deaktivieren', 'verlassen', 'verlasse', 'abschalten', 'raus aus'
        )
        if any(trigger in lowered for trigger in exit_triggers):
            self._set_conversation_mode('standard')
            self._set_voice_mode('neutral')
            self.context.pop('neural_last_sources', None)
            return 'Neural Mode deaktiviert. Ich arbeite wieder im Standardmodus.'

        self._set_conversation_mode('neural')
        self._set_voice_mode('professionell')

        query: Optional[str] = None
        if match and getattr(match, 'entities', None):
            for key in ('topic', 'topic_alt', 'topic_info'):
                value = match.entities.get(key)
                if value:
                    query = self._extract_search_query(str(value)) or str(value)
                    break
        if not query and text:
            cleaned = re.sub(r'(?i)neural(?:er)?\s*modus', '', text)
            cleaned = re.sub(r'(?i)aktiviere|aktivieren|schalte ein|starte', '', cleaned)
            query = self._extract_search_query(cleaned) or cleaned.strip(' :-,')

        if query:
            neural_response = self._run_neural_synthesis(query)
            if neural_response:
                return neural_response
            return (
                f'Neural Mode aktiv, aber ich konnte zu "{query}" keine verknuepfbaren Quellen finden. '
                'Bitte probieren Sie es mit einer anderen Fragestellung.'
            )

        return (
            "Neural Mode ist jetzt aktiv. Ich verknuepfe Informationen aus lokalen und externen Quellen. "
            "Stellen Sie mir eine Frage, z. B. \"Analysiere Auswirkungen der Energiewende auf Deutschland\"."
        )



    def handle_emergency_mode(self, text: str = '', match: Optional[IntentMatch] = None) -> str:
        """Aktiviert das Sicherheits-Notfallprotokoll (SNP-01-Lokal)."""
        lowered = (text or '').lower()
        actions = self._extract_emergency_actions(lowered)

        immediate_results: Dict[str, bool] = {}
        if actions:
            try:
                immediate_results = self.system_control.trigger_emergency(list(actions))
            except Exception as exc:
                self.logger.error(f"Notfallaktionen fehlgeschlagen: {exc}")

        incident = None
        if self.security_protocol is not None:
            level = self._determine_emergency_priority(lowered)
            reason = text or 'Sicherheitsmodus angefordert'
            try:
                incident = self.security_protocol.activate(level, reason, initiated_by='voice-command')
            except Exception as exc:
                self.logger.error(f"Sicherheitsprotokoll konnte nicht ausgeführt werden: {exc}", exc_info=True)

        summary_lines: List[str] = []
        if incident is not None:
            summary_lines.append(f"Sicherheits-Notfallprotokoll ausgelöst ({incident.level.label()}).")
            final_message = None
            if isinstance(getattr(incident, 'results', None), dict):
                final_message = incident.results.get('final_message')
            if final_message:
                summary_lines.append(final_message)
            if incident.archive_path:
                summary_lines.append(f"Snapshot: {incident.archive_path}")
            if incident.report_path:
                summary_lines.append(f"Bericht: {incident.report_path}")

        if actions:
            summary_lines.append("Sofortmaßnahmen:")
            for action in actions:
                success = immediate_results.get(action, False)
                summary_lines.append(f"- {action}: {'OK' if success else 'Fehlgeschlagen'}")

        if not summary_lines:
            summary_lines.append("Sicherheitsmodus konnte nicht aktiviert werden.")

        context_payload: Dict[str, Any] = {
            'timestamp': datetime.datetime.now().isoformat(),
            'actions': list(actions),
            'results': immediate_results,
        }
        if incident is not None:
            context_payload['incident'] = incident.as_dict() if hasattr(incident, 'as_dict') else str(incident)
        self.context['last_emergency'] = context_payload

        return "\n".join(summary_lines)

    def handle_voice_enroll(self, text: str = '', match: Optional[IntentMatch] = None) -> str:
        """Legt eine neue Stimmprobe an oder aktualisiert sie."""
        if not self.voice_biometrics:
            return "Die Stimmregistrierung ist nicht aktiv. Bitte aktiviere die Stimmidentifikation in den Einstellungen."

        metadata = self.context.get('last_metadata') or {}
        audio_blob = metadata.get('audio_blob')
        if not audio_blob:
            return (
                "Ich habe in dieser Eingabe keinen Audiostream erhalten. "
                "Bitte sage erneut \"Stimmprobe aufnehmen\" und sprich dabei einen kurzen Satz von mindestens 3 Sekunden."
            )

        profile_name = "default"
        if match and getattr(match, "entities", None):
            profile_candidate = match.entities.get("profile")
            if profile_candidate:
                profile_name = str(profile_candidate).strip().lower() or profile_name
        else:
            lowered = (text or "").strip().lower()
            normalized = lowered
            if "f\u00fcr" in normalized:
                normalized = normalized.replace("f\u00fcr", "fuer")
            if "fuer" in normalized:
                tail = normalized.split("fuer", 1)[1].strip()
                if tail:
                    profile_name = tail.split()[0]

        profile_name = ''.join(ch for ch in profile_name if ch.isalnum() or ch in ("_", "-")) or "default"

        try:
            success = self.voice_biometrics.enroll_from_audio(audio_blob, profile=profile_name)
        except Exception as exc:
            self.logger.error(f"Stimmprobe konnte nicht gespeichert werden: {exc}")
            return "Die Stimmprobe konnte nicht gespeichert werden. Bitte versuche es spaeter erneut."

        if success:
            profiles = self.context.setdefault('voice_profiles', [])
            if isinstance(profiles, list) and profile_name not in profiles:
                profiles.append(profile_name)
            return (
                f"Stimmprobe fuer Profil '{profile_name}' gespeichert. "
                "Ich verwende diese Aufnahme ab jetzt fuer Sprachfreigaben."
            )
        return "Die Stimmprobe war zu kurz oder unverstaendlich. Bitte versuche es erneut und sprich einen vollstaendigen Satz."

    def _extract_emergency_actions(self, text: str) -> Set[str]:
        actions: Set[str] = set()
        if not text:
            return {'lock', 'alarm'}
        if any(token in text for token in ('netz', 'wlan', 'internet', 'offline', 'disconnect', 'netzwerk')):
            actions.add('disconnect')
        if any(token in text for token in ('alarm', 'sirene', 'ton', 'laut')):
            actions.add('alarm')
        if any(token in text for token in ('sperr', 'lock', 'bildschirm sperren', 'pc sperren')):
            actions.add('lock')
        if any(token in text for token in ('kamera', 'kamera an', 'kamera aktivieren')):
            actions.add('camera')
        if not actions:
            actions = {'lock', 'alarm'}
        return actions

    def _determine_emergency_priority(self, text: str) -> PriorityLevel:
        if not text:
            return PriorityLevel.MAJOR
        if any(token in text for token in ('stufe 1', 'kritisch', 'kompromitt', 'datenleck', 'leak')):
            return PriorityLevel.CRITICAL
        if any(token in text for token in ('stufe 2', 'schwer', 'kernel', 'core', 'major')):
            return PriorityLevel.MAJOR
        if any(token in text for token in ('stufe 3', 'mittel', 'tts', 'stt', 'wissensmodul', 'module')):
            return PriorityLevel.MODERATE
        if any(token in text for token in ('stufe 4', 'leicht', 'session', 'neu starten')):
            return PriorityLevel.MINOR
        return PriorityLevel.from_text(text)
    def handle_system_status(self, text: str = '', match: Optional[IntentMatch] = None):

        """Gibt den aktuellen Systemstatus zurueck."""

        try:

            status = self.system_control.get_system_status() or {}

            cpu = float(status.get('cpu', 0))

            memory = float(status.get('memory', 0))

            disk = float(status.get('disk', 0))

            return (

                "Hier ist der aktuelle Systemstatus: "

                f"CPU {cpu:.0f}% - Arbeitsspeicher {memory:.0f}% - Datentraeger {disk:.0f}%."

            )

        except Exception as exc:

            self.logger.error(f"Fehler beim Systemstatus: {exc}")

            return "Entschuldigung, der Systemstatus konnte nicht ermittelt werden."



    def handle_create_file(self, text: str = '', match: Optional[IntentMatch] = None) -> str:
        """Erstellt Dateien und schreibt optional Inhalt hinein."""
        raw_text = (text or '').strip()
        if not raw_text:
            return "Bitte nenne mir den Dateinamen und optional den Inhalt fuer die Datei."
        entities = match.entities if match and getattr(match, "entities", None) else None
        raw_lower = raw_text.lower()
        target_path: Optional[str] = None
        location_hint: Optional[str] = None
        if isinstance(entities, dict):
            for key in ('path', 'file', 'filename', 'datei', 'target'):
                value = entities.get(key)
                if value:
                    target_path = str(value)
                    break
        if not target_path:
            target_path = self._extract_file_reference(raw_text)
        if not target_path:
            inferred_path, inferred_hint = self._infer_creation_target(raw_text)
            if inferred_path:
                target_path = inferred_path
                location_hint = inferred_hint
        if not target_path:
            return "Ich konnte keinen Dateinamen erkennen. Bitte gib mir den Namen inklusive Erweiterung."
        path_clean = target_path.strip().strip('"').strip("'").rstrip('?!;,')
        if not path_clean:
            return "Bitte formuliere den Dateinamen klar, damit ich die Datei anlegen kann."
        content_text, missing_content = self._extract_file_write_content(
            raw_text,
            path_clean,
            entities if isinstance(entities, dict) else None,
        )
        if missing_content and not content_text:
            return "Bitte teile mir den konkreten Inhalt mit, den ich in die Datei schreiben soll."
        body = self._strip_code_fences(content_text or "")
        template_note: Optional[str] = None
        if not body or self._looks_like_plain_language(body):
            generated, note = self._generate_content_from_description(raw_text)
            if generated:
                body = generated
                template_note = note
        if self._looks_like_plain_language(body) and not template_note:
            if any(keyword in raw_lower for keyword in ('code', 'programm', 'program', 'script', 'skript')):
                return "Bitte beschreibe den gewuenschten Code genauer oder gib den Inhalt direkt an."
        overwrite = self._detect_overwrite_request(raw_text)
        try:
            result = self.system_control.create_file(
                path_clean,
                content=body,
                overwrite=overwrite,
            )
        except FileExistsError:
            return (
                f"Die Datei {path_clean} existiert bereits. Sage 'ueberschreibe', "
                "wenn ich sie ersetzen soll."
            )
        except PermissionError as perm_error:
            self.logger.warning("Keine Schreibrechte fuer %s: %s", path_clean, perm_error)
            return (
                f"Ich habe keine Schreibrechte fuer {path_clean}. "
                "Bitte passe die Sicherheitsrichtlinie an oder waehle einen erlaubten Speicherort."
            )
        except Exception as exc:
            self.logger.error(f"Fehler beim Erstellen der Datei {path_clean}: {exc}", exc_info=True)
            return f"Beim Erstellen von {path_clean} ist ein Fehler aufgetreten: {exc}"
        result_path: Union[str, Path] = path_clean
        if isinstance(result, dict):
            info = result.get('info') or {}
            result_path = info.get('path') or result.get('path') or path_clean
        action = 'aktualisiert' if overwrite else 'erstellt'
        result_path_str = str(result_path)
        segments: List[str] = [f"Die Datei {result_path_str} wurde {action}."]
        if body:
            segments.append(f"Ich habe {len(body)} Zeichen geschrieben.")
        else:
            segments.append("Die Datei ist aktuell leer.")
        if location_hint and location_hint.lower() not in result_path_str.lower():
            segments.append(f"Ziel: {location_hint}.")
        if template_note:
            segments.append(f"Generiert: {template_note}.")
        self.context['last_created_file'] = result_path_str
        recent_files = self.context.get('recent_files')
        if not isinstance(recent_files, list):
            recent_files = []
        recent_files.append(result_path_str)
        self.context['recent_files'] = recent_files[-10:]
        return " ".join(segments)

    def handle_open_program(self, text: str = '', match: Optional[IntentMatch] = None):

        """Oeffnet ein Programm anhand des Intent-Matchings."""

        program_key = self._resolve_program_key(text, match)

        if not program_key:

            return 'Welches Programm soll ich oeffnen? Bitte nennen Sie es genauer.'

        display = self.program_display_names.get(program_key, program_key)

        if self.system_control.open_program(program_key):

            return f"{display} wurde fuer Sie geoeffnet."

        return f"{display} konnte nicht geoeffnet werden."



    def handle_close_program(self, text: str = '', match: Optional[IntentMatch] = None):

        """Schliesst ein Programm anhand des Intent-Matchings."""

        program_key = self._resolve_program_key(text, match)

        if not program_key:

            return 'Welches Programm soll ich schliessen? Bitte nennen Sie es genauer.'

        display = self.program_display_names.get(program_key, program_key)

        if self.system_control.close_program(program_key):

            return f"{display} wurde geschlossen."

        return f"{display} konnte nicht geschlossen werden."



    def handle_music_command(self, text: str = '', match: Optional[IntentMatch] = None) -> str:

        """Steuert YouTube-Wiedergabe über den MediaRouter."""

        if not getattr(self, "media_router", None):

            return "Die Mediensteuerung steht derzeit nicht zur Verfügung."

        self.context['skip_llm_fallback'] = True

        raw_command = text or (match.raw_text if match else "") or (match.matched_text if match else "")

        normalized = self._normalize_user_text(raw_command)
        normalized = self._normalize_music_command_text(normalized)
        lowered = normalized.lower()

        entities = (match.entities if match and match.entities else {}) or {}

        target = entities.get("target") or entities.get("medium") or "youtube"

        action = (entities.get("action") or "").lower().strip()

        track = entities.get("track") or ""

        if not action:

            action = self._infer_music_action(lowered)

        if action in {"volume_up", "volume_down"}:

            direction = "up" if action == "volume_up" else "down"

            success = self.media_router.adjust_volume(direction, steps=2)
            self._sync_media_state()

            if success:

                return "Ich passe die Lautstärke an."

            return "Ich konnte keine laufende YouTube-Wiedergabe finden."

        if action == "mute":

            success = self.media_router.mute_toggle()
            self._sync_media_state()

            return "Ich habe die Wiedergabe stummgeschaltet." if success else "Ich konnte keine laufende YouTube-Wiedergabe finden."

        if action == "pause":

            success = self.media_router.pause()
            self._sync_media_state()

            return "Wiedergabe angehalten." if success else "Ich konnte keine laufende YouTube-Wiedergabe finden."

        if action in {"resume", "continue"}:

            success = self.media_router.resume()
            self._sync_media_state()

            return "Wiedergabe fortgesetzt." if success else "Ich konnte keine laufende YouTube-Wiedergabe finden."

        if action == "next":

            success = self.media_router.next_track()
            self._sync_media_state()

            return "Ich springe zum nächsten Titel." if success else "Ich konnte keine laufende YouTube-Wiedergabe finden."

        if action == "previous":

            success = self.media_router.previous_track()
            self._sync_media_state()

            return "Ich springe zurück zum vorherigen Titel." if success else "Ich konnte keine laufende YouTube-Wiedergabe finden."

        if not track:

            track = self._extract_music_track(lowered)

        if not track and action == "play":

            router_state = self.media_router.state()

            if router_state.get("youtube_active"):

                resumed = self.media_router.resume()
                self._sync_media_state()
                return "Wiedergabe fortgesetzt." if resumed else "Ich konnte keine laufende YouTube-Wiedergabe finden."

        if not track:

            router_state = self.media_router.state()

            track = (router_state or {}).get('track') or ""

        if not track:

            last_media = self.context.get('media_state', {})

            track = (last_media or {}).get('last_track') or ""

        if not track:

            return "Welchen Titel soll ich auf YouTube abspielen?"

        cleaned_track = track.strip()
        if cleaned_track.isdigit():
            return 'Bitte nenne den Titel oder Interpreten, nicht nur eine Zahl.'

        result = self.media_router.play(track, target=target)

        if result.get("success") and result.get("exact"):

            message = f"YouTube >> {track}"

        elif result.get("success"):

            message = f"YouTube-Suche fuer {track} geoeffnet."

        else:

            message = "YouTube konnte nicht gestartet werden."

        self._sync_media_state()

        return message



    def handle_knowledge_search(self, text: str = '', match: Optional[IntentMatch] = None):

        """Sucht nach Informationen im lokalen oder externen Wissen."""

        query = None

        if match and match.entities:

            for key in ('topic', 'topic_alt', 'topic_info'):

                value = match.entities.get(key)

                if value:

                    query = value

                    break

        if query:

            query = self._extract_search_query(query) or query

        if not query:

            query = self._extract_search_query(text) or ''

        query = query.strip()

        if not query:

            return 'Worueber moechten Sie Informationen? Bitte formulieren Sie die Frage konkret.'

        if self.context.get('conversation_mode') == 'neural':
            neural_response = self._run_neural_synthesis(query)
            if neural_response:
                return neural_response
            # Falls keine Quellen verknuepft werden konnten, weiter mit Standardlogik

        # Minimal-invasive Policy-Routing gemaess Vorgaben
        ql = query.lower()

        # 1) Externe News / Live-Daten nur bei expliziten Hinweisen
        news_triggers = ('aktuell', 'heute', 'jetzt', 'news', 'wetter', 'boerse', 'boersen', 'maerkte', 'maerkte')
        if any(t in ql for t in news_triggers):
            result = None
            try:
                # Bevorzugt externe Quellen
                result = self.knowledge_manager.search_external_sources(query)
            except Exception as exc:
                self.logger.error(f"News/Live-Abfrage fehlgeschlagen: {exc}")
            if result:
                return result.strip()
            # Fallback auf generische Suche
            result = self.knowledge_manager.search_knowledge(query)
            if result:
                return result.strip()
            return f'Zu "{query}" habe ich derzeit keine aktuellen Daten gefunden.'

        # 2) Projektdateien nur bei explizitem Projektbezug
        project_triggers = (
            'projekt', 'projektordner', 'repo', 'repository', 'status', 'zeige status'
        )
        wants_project = any(t in ql for t in project_triggers) or bool(self._extract_file_reference(query))
        if wants_project:
            # Bevorzugt lokale Wissensbasis
            local = self.knowledge_manager.search_local_knowledge(query)
            if local:
                return local.strip()
            # Leichte Hilfeausgabe statt unkontrolliertem externen Lookup
            return (
                'Ich habe keinen passenden lokalen Eintrag gefunden. '
                'Nennen Sie mir bitte den genauen Datei- oder Ordnernamen (z. B. "zeige Status im Projektordner").'
            )

        # 3) Persoenliche Daten nur mit Bestaetigung (keine automatische Suche)
        personal_triggers = ('meine dateien', 'meine dokumente', 'persoenlich', 'persoenlich', 'private', 'privat')
        if any(t in ql for t in personal_triggers):
            self.context['pending_confirmation'] = {
                'action': 'search_personal',
                'query': query,
            }
            return (
                'Soll ich in persoenlichen Daten suchen? Bitte bestaetigen Sie dies explizit '
                '(z. B. "ja, suche in meinen Dokumenten nach <Thema>").'
            )

        # 4) Philosophie / Allgemeine Fragen: direkt LLM, keine Dateisuche
        philosophy_triggers = ('warum', 'philosophie', 'philosophisch', 'allgemein', 'meinung', 'was denkst du')
        if any(t in ql for t in philosophy_triggers):
            return self.handle_ai_chat(query)

        # 5) Allgemeines Wissen: immer externe APIs bevorzugen, Antwort schoen in Deutsch
        try:
            result = self.knowledge_manager.search_external_sources(query)
            if result:
                return result.strip()
        except Exception as exc:
            self.logger.error(f"Externe Wissenssuche fehlgeschlagen: {exc}")

        # Fallback: kombinierte Suche (lokal + extern wie bisher)
        result = self.knowledge_manager.search_knowledge(query)
        if result:
            return result.strip()

        return f'Zu "{query}" habe ich aktuell keine Quelle gefunden.'



    def handle_time_date(self, text: str = '', match: Optional[IntentMatch] = None):

        """Kombinierte Rueckgabe von Zeit und Datum."""

        now = datetime.datetime.now()

        return now.strftime('Es ist %H:%M Uhr am %d.%m.%Y.')



    def handle_time_request(self, text: str = '', match: Optional[IntentMatch] = None):

        """Antwortet auf eine Uhrzeitanfrage."""

        return datetime.datetime.now().strftime('Es ist %H:%M Uhr.')



    def handle_date_request(self, text: str = '', match: Optional[IntentMatch] = None):

        """Antwortet auf eine Datumsanfrage."""

        now = datetime.datetime.now()

        weekday_names = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag']

        weekday = weekday_names[now.weekday()] if 0 <= now.weekday() < len(weekday_names) else 'Heute'

        return f"Heute ist {weekday}, der {now.strftime('%d.%m.%Y')}."



    def handle_goodbye(self, text: str = '', match: Optional[IntentMatch] = None):

        """Verabschiedet sich freundlich."""

        return 'Bis bald! Wenn Sie mich brauchen, bin ich sofort bereit.'

    def _normalize_user_text(self, value: str) -> str:

        if not value:

            return ''

        simplified = value.translate(self._normalize_trans) if hasattr(self, '_normalize_trans') else value

        return re.sub(r'\s+', ' ', simplified).strip()


    def _looks_like_incomplete_command(self, text: str) -> bool:
        if not text:
            return True
        normalized = self._normalize_user_text(text).lower()
        if not normalized:
            return True
        if normalized in self._short_command_whitelist:
            return False
        # if the command already contains recognised keywords, accept it
        for keyword in self._intent_keyword_lookup.keys():
            if keyword in normalized or HotwordManager.approximate_contains(normalized, keyword, cutoff=0.9):
                return False
        words = normalized.split()
        if len(words) == 1:
            word = words[0]
            if word in self._filler_words:
                return True
            return len(word) <= 2
        if len(words) == 2 and all(word in self._filler_words for word in words):
            return True
        return False


    def _collect_intent_hints(self, normalized_text: str) -> Dict[str, object]:
        lowered = (normalized_text or '').lower()
        bias: Dict[str, float] = {}
        hint_tokens: List[str] = []
        if not lowered:
            return {"engine_input": normalized_text, "bias": bias, "program_key": None, "tokens": []}

        for intent, config in (self._intent_hint_config or {}).items():
            keywords = config.get('keywords') if isinstance(config, dict) else ()
            if not keywords:
                continue
            if self._intent_hit(lowered, keywords):
                boost = float(config.get('boost', 0.0)) if isinstance(config, dict) else 0.0
                hint_token = str(config.get('hint') or f"intent_{intent}")
                hint_tokens.append(hint_token)
                if boost:
                    bias[intent] = max(bias.get(intent, 0.0), boost)

        program_key = self._locate_program_keyword(lowered)
        if program_key:
            hint_tokens.append(f"program_{program_key}")
            if 'open_program' in (self._intent_hint_config or {}):
                bias['open_program'] = max(bias.get('open_program', 0.0), 0.15)

        engine_input = normalized_text
        if hint_tokens:
            engine_input = f"{normalized_text} {' '.join(hint_tokens)}"
        return {
            "engine_input": engine_input,
            "bias": bias,
            "program_key": program_key,
            "tokens": hint_tokens,
        }


    def _intent_hit(self, text: str, keywords: Sequence[str]) -> bool:
        if not text or not keywords:
            return False
        for keyword in keywords:
            key = (keyword or '').strip()
            if not key:
                continue
            if key in text:
                return True
            if HotwordManager.approximate_contains(text, key, cutoff=0.88):
                return True
        return False

    def _sync_media_state(self) -> None:
        if not getattr(self, "media_router", None):
            return
        try:
            router_state = self.media_router.state()
        except Exception:
            router_state = {}
        snapshot = {
            'last_track': router_state.get('track'),
            'target': router_state.get('target'),
            'url': router_state.get('url'),
            'youtube_active': router_state.get('youtube_active'),
            'edge_running': router_state.get('edge_running'),
            'timestamp': datetime.datetime.now().isoformat(),
        }
        self.context['media_state'] = snapshot

    def _infer_music_action(self, lowered_text: str) -> str:
        """Heuristik zur Aktionsbestimmung fuer Musikbefehle."""
        if self._text_contains_any(lowered_text, ('pause', 'pausiere', 'stopp', 'stoppe', 'halt an', 'halte an', 'anhalten')):
            return 'pause'
        if self._text_contains_any(lowered_text, (
            'weiter spielen',
            'weiterspielen',
            'spiel weiter',
            'fortsetzen',
            'weiterlaufen',
            'resume',
            'setze die wiedergabe fort',
            'setze wiedergabe fort',
            'wiedergabe fortsetzen',
            'wiedergabe fort',
            'setze fort',
            'weiter abspielen',
        )):
            return 'resume'
        if self._text_contains_any(lowered_text, ('naechstes lied', 'nächstes lied', 'naechstes video', 'nächstes video', 'weiter', 'skip', 'nächster titel', 'naechster titel', 'next')):
            return 'next'
        if self._text_contains_any(lowered_text, ('vorheriges lied', 'voriges lied', 'vorheriges video', 'zurueck', 'zurück', 'vorher', 'previous', 'zurueckspulen', 'zurückspulen')):
            return 'previous'
        if self._text_contains_any(lowered_text, ('mach lauter', 'lauter', 'lautstaerke hoch', 'lautstärke hoch', 'erhoehe lautstaerke', 'erhöhe lautstärke', 'lauter machen')):
            return 'volume_up'
        if self._text_contains_any(lowered_text, ('mach leiser', 'leiser', 'lautstaerke runter', 'lautstärke runter', 'senke lautstaerke', 'senke die lautstärke', 'leiser machen')):
            return 'volume_down'
        if self._text_contains_any(lowered_text, ('mute', 'stummschalten', 'stumm schalten', 'stumm', 'lautlos')):
            return 'mute'
        return 'play'

    def _normalize_music_command_text(self, text: str) -> str:
        if not text:
            return ''
        normalized = text.lower()
        replacements = {
            "ab spielen": "abspielen",
            "ab zu spielen": "abzuspielen",
            "spiel musik ab": "musik abspielen",
            "spiele musik ab": "musik abspielen",
            "spiel die musik": "spiel musik",
            "spiele die musik": "spiel musik",
            "spiel bitte": "spiel",
            "spiele bitte": "spiel",
            "spiel mal": "spiel",
            "spiele mal": "spiel",
            "mach bitte": "mach",
            "setze die wiedergabe fort": "wiedergabe fortsetzen",
            "setze wiedergabe fort": "wiedergabe fortsetzen",
            "spiel die wiedergabe fort": "wiedergabe fortsetzen",
            "setze die musik fort": "musik fortsetzen",
            "weiter abspielen": "weiter abspielen",
        }
        for src, dst in replacements.items():
            normalized = re.sub(rf'\b{re.escape(src)}\b', dst, normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        return normalized

    def _extract_music_track(self, lowered_text: str) -> str:
        """Entfernt Steuerwörter und extrahiert den Rest als Titel."""
        working = lowered_text
        removal_patterns = [
            'hey jarvis',
            'jarvis',
            'spiel bitte',
            'spiele bitte',
            'spiel mal',
            'spiele mal',
            'spiele',
            'spiel',
            'auf youtube',
            'youtube',
            'bitte',
            'ab',
            'die musik',
            'musik',
            'den song',
            'den titel',
            'das lied',
            'lied',
            'song',
            'video',
            'die wiedergabe',
            'wiedergabe',
            'musik fortsetzen',
            'fuer mich',
            'fuer mich',
            'jetzt',
        ]
        for phrase in removal_patterns:
            working = re.sub(rf'\b{re.escape(phrase)}\b', ' ', working)
        working = working.strip(' ,-.')
        words = [word for word in re.split(r'\s+', working) if word]
        if not words:
            return ''
        stopwords = getattr(self, '_music_stopwords', set())
        while words and words[0] in stopwords:
            words.pop(0)
        while words and words[-1] in stopwords:
            words.pop()
        if not words:
            return ''
        if all(word in stopwords for word in words):
            return ''
        candidate = " ".join(words).strip(" ,-.")
        if len(candidate) <= 2:
            return ''
        return candidate

    def _text_contains_any(self, text: str, keywords: Sequence[str]) -> bool:
        if not text:
            return False
        for keyword in keywords:
            if keyword in text:
                return True
        return False




    def handle_help(self, text: str = '', match: Optional[IntentMatch] = None):

        """Erklaert die wichtigsten Funktionen von Jarvis."""

        help_lines = [
            'Ich unterstuetze Sie bei folgenden Aufgaben:',
            '- Programme starten und beenden (z. B. "oeffne Notepad")',
            '- Systemstatus und Ressourcen anzeigen',
            '- Informationen aus lokalen Dateien und dem Internet recherchieren',
            '- Uhrzeit, Datum und organisatorische Fragen beantworten',
            '- Freie Dialoge ueber das integrierte Sprachmodell fuehren'
        ]

        if self.learning_manager:
            top_commands = self.learning_manager.get_top_commands(limit=3)
            if top_commands:
                help_lines.append('')
                help_lines.append('Haeufig verwendete Befehle:')
                for command, count in top_commands:
                    help_lines.append(f"- {command} ({count}x)")
            behavior = self.learning_manager.get_behavior_summary()
            if behavior:
                peak = behavior.get('peak_hour')
                quiet = behavior.get('quiet_hour')
                info_bits = []
                if isinstance(peak, int):
                    info_bits.append(f"Peak-Aktivitaet ca. {peak:02d}:00 Uhr")
                if isinstance(quiet, int):
                    info_bits.append(f"Ruhephase ca. {quiet:02d}:00 Uhr")
                if info_bits:
                    help_lines.append('')
                    help_lines.append('Verhaltensprofil: ' + ' | '.join(info_bits))

        separator = '\n'

        return separator.join(help_lines)



    def _intent_to_command_type(self, match: Optional[IntentMatch]) -> Optional[str]:

        if not match:

            return None

        return match.name



    def handle_unknown_command(self, text):

        """Fallback, falls kein Intent passt."""

        trimmed = (text or '').strip()

        if self.context.get('conversation_mode') == 'entertainment':
            last_kind = self.context.get('entertainment_last_type') or 'smalltalk'
            if last_kind == 'jokes':
                pool = self._entertainment_material['jokes']
            elif last_kind == 'facts':
                pool = self._entertainment_material['facts']
            else:
                pool = self._entertainment_material['smalltalk'] + self._entertainment_material['prompts']
            choice = random.choice(pool)
            self._set_voice_mode('humorvoll')
            return choice

        skip_llm = bool(self.context.pop('skip_llm_fallback', False))

        if self.llm_manager and trimmed and not skip_llm:

            try:

                llm_response = self.llm_manager.generate_response(
                    trimmed,
                    use_case=self.context.get('last_use_case'),
                    task_hint=self.context.get('logic_path'),
                )

                if llm_response:

                    return llm_response.strip()

            except Exception as exc:

                self.logger.error(f"LLM-Fallback schlug fehl: {exc}")

        suggestions = self.find_similar_commands(trimmed)

        if suggestions:

            return (

                'Das habe ich nicht eindeutig verstanden. '

                f"Meinten Sie vielleicht: {', '.join(suggestions[:3])}?"

            )

        return 'Das habe ich nicht verstanden. Formulieren Sie den Wunsch bitte noch einmal.'











    def find_similar_commands(self, text):

        """Findet sssssssshnliche Befehle basierend auf Textsssssssshnlichkeit"""

        suggestions = []

        text_lower = text.lower()

        

        for command_type, data in self.command_patterns.items():

            patterns = data.get('patterns', [])

            for pattern in patterns:

                # Einfache ssssssssss?hnlichkeitsprssssssssfung

                common_words = set(text_lower.split()) & set(pattern.split())

                if common_words:

                    suggestions.append(pattern)

        

        return suggestions

    

    def add_custom_command(self, pattern, response, category='custom'):

        """Fssssssssgt benutzerdefinierten Befehl hinzu"""

        try:

            if category not in self.command_patterns:

                self.command_patterns[category] = {

                    'patterns': [],

                    'responses': []

                }

            

            self.command_patterns[category]['patterns'].append(pattern.lower())

            self.command_patterns[category]['responses'].append(response)

            

            self.save_command_patterns()

            self.logger.info(f"Neuer Befehl hinzugefssssssssgt: {pattern}")

            

            return True

        except Exception as e:

            self.logger.error(f"Fehler beim Hinzufssssssssgen des Befehls: {e}")

            return False

    

    def handle_ai_chat(self, text):

        """Behandelt erweiterte AI-Chat Anfragen"""

        try:

            if self.llm_manager:

                # LLM fuer komplexere Antworten verwenden

                response = self.llm_manager.generate_response(
                    text,
                    use_case=self.context.get('last_use_case'),
                    task_hint=self.context.get('logic_path'),
                )

                if response:

                    return response

            

            # Fallback auf erweiterte Pattern-basierte Antworten

            return self.handle_intelligent_fallback(text)

            

        except Exception as e:

            self.logger.error(f"Fehler bei AI-Chat: {e}")

            return "Entschuldigung, ich konnte Ihre Anfrage nicht richtig verarbeiten."

    def handle_intelligent_fallback(self, text):

        """Erzeugt strukturierte Standardantworten fuer schwierigere Anfragen."""

        text_lower = (text or '').lower()

        if any(word in text_lower for word in ['was ist', 'wie funktioniert', 'erklaere', 'erklaer', 'was sind']):

            knowledge_result = self.knowledge_manager.search_knowledge(text)

            if knowledge_result:

                return knowledge_result

            return 'Ich recherchiere das gern naeher. Geben Sie mir einen Moment oder praezisieren Sie die Frage.'

        if any(word in text_lower for word in ['python', 'programmieren', 'code', 'software', 'algorithmus']):

            return 'Zu Programmier- oder Softwarethemen helfe ich gern. Beschreiben Sie bitte konkret, wobei Sie Unterstuetzung brauchen.'

        if any(word in text_lower for word in ['meinung', 'denkst du', 'findest du']):

            return 'Ich habe keine eigenen Meinungen, aber ich kann Fakten, Perspektiven und Quellen bereitstellen.'

        if any(word in text_lower for word in ['geschichte', 'gedicht', 'kreativ', 'schreibe']):

            return 'Wenn Sie einen kreativen Text wuenschen, nennen Sie bitte Form, Stil und ungefaehre Laenge.'

        if any(word in text_lower for word in ['berechne', 'rechne', 'mathematik', 'formel']):

            return 'Nennen Sie mir bitte die konkrete Rechnung oder Formel, dann rechne ich diese Schritt fuer Schritt durch.'

        return 'Das klingt komplex. Beschreiben Sie mir bitte genauer, was Sie dazu wissen oder erreichen moechten.'


