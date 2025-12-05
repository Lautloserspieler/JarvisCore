"""Speech recognition module for J.A.R.V.I.S."""

from __future__ import annotations

import math
import re
import threading
import time
import copy
import os
import base64
from array import array
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Callable, List, Optional, Sequence, Tuple

import numpy as np
try:
    import pyaudio  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    pyaudio = None  # type: ignore
try:
    from faster_whisper import WhisperModel  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    WhisperModel = None  # type: ignore

try:
    import torch
except Exception:  # pragma: no cover - optional dependency
    torch = None

from utils.logger import Logger
from models.download_whisper import WhisperDownloader
from core.emotion_analyzer import EmotionAnalyzer
from core.hotword_manager import HotwordManager
import requests


WHISPER_TRANSCRIBE_OPTIONS = {
    "language",
    "task",
    "beam_size",
    "best_of",
    "patience",
    "length_penalty",
    "repetition_penalty",
    "no_repeat_ngram_size",
    "temperature",
    "compression_ratio_threshold",
    "log_prob_threshold",
    "no_speech_threshold",
    "condition_on_previous_text",
    "initial_prompt",
    "prompt_reset_on_temperature",
    "hotwords",
    "audio_chunk_seconds",
    "vad_filter",
    "vad_parameters",
    "without_timestamps",
    "word_timestamps",
    "prepend_punctuations",
    "append_punctuations",
    "max_new_tokens",
    "chunk_length",
    "clip_timestamps",
    "hallucination_silence_threshold",
    "temperature_increment_on_fallback",
    "compression_ratio_threshold_increment_on_fallback",
    "log_prob_threshold_increment_on_fallback",
}

PROFILE_META_KEYS = {"max_history_chars"}

TAIL_FILLER_WORDS = ("und", "aber", "also")
DEFAULT_IGNORED_PHRASES: Tuple[str, ...] = (
    "file manager",
    "dialog",
    "windows sicherheitsmeldung",
    "information box",
)
DEFAULT_COMMAND_ALIASES: Dict[str, str] = {
    "notfall protokoll": "notfallprotokoll",
    "notfall-protokoll": "notfallprotokoll",
    "notfall protokol": "notfallprotokoll",
    "notfallprotokoll zwei": "notfallprotokoll stufe 2",
    "notfallprotokoll stufe zwei": "notfallprotokoll stufe 2",
    "notfallprotokoll stufe zwei bitte": "notfallprotokoll stufe 2",
    "starte notfall protokoll": "starte notfallprotokoll",
    "starte notfall protokoll stufe zwei": "starte notfallprotokoll stufe 2",
    "starte notfallprotokoll zwei": "starte notfallprotokoll stufe 2",
}
NUMBER_WORD_MAP: Dict[str, str] = {
    "null": "0",
    "eins": "1",
    "eine": "1",
    "ein": "1",
    "ersten": "1",
    "zwei": "2",
    "zweiten": "2",
    "drei": "3",
    "dritten": "3",
    "vier": "4",
    "fuenf": "5",
    "fünf": "5",
    "sechs": "6",
    "sieben": "7",
    "acht": "8",
    "neun": "9",
}


@dataclass
class SpeechRecognizerConfig:
    """Configuration container for the speech recogniser."""

    sample_rate: int = 16000
    chunk_size: int = 4096
    channels: int = 1
    wake_words: List[str] = field(default_factory=lambda: ["jarvis", "hey jarvis", "hallo jarvis"])
    wake_word_enabled: bool = True
    command_timeout: float = 1.7
    duplicate_filter: bool = True
    input_device: Optional[str] = None
    input_device_index: Optional[int] = None
    preferred_input_keywords: List[str] = field(default_factory=list)
    whisper_model: str = "distil-large-v3"
    model_id: Optional[str] = None
    device: str = "cpu"
    compute_type: str = "int8"
    fallback_language: str = "de"
    max_history_chars: int = 1200
    silence_timeout: float = 0.7
    max_command_duration: float = 3.8
    default_mode: str = "command"
    command_hotwords: List[str] = field(default_factory=lambda: ["notfall", "notfallprotokoll", "alarmmodus"])
    command_aliases: Dict[str, str] = field(default_factory=lambda: dict(DEFAULT_COMMAND_ALIASES))
    ignored_phrases: List[str] = field(default_factory=lambda: list(DEFAULT_IGNORED_PHRASES))
    mode_profiles: Dict[str, Dict[str, Any]] = field(
        default_factory=lambda: {
            "command": {
                "language": "de",
                "beam_size": 1,
                "temperature": 0.0,
                "vad_filter": True,
                "vad_parameters": {
                    "threshold": 0.62,
                    "min_speech_duration_ms": 300,
                    "min_silence_duration_ms": 650,
                    "speech_pad_ms": 180,
                    "max_speech_duration_s": 4.0,
                },
                "condition_on_previous_text": False,
                "no_speech_threshold": 0.6,
                "initial_prompt": (
                    "Deutschsprachige Kurzbefehle wie 'öffne', 'starte', 'lauter', "
                    "'leiser', 'stopp', 'abbrechen', 'zeige status', "
                    "'wie spät ist es', 'suche', 'spiele musik'."
                ),
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
                    "speech_pad_ms": 150,
                },
                "condition_on_previous_text": True,
                "no_speech_threshold": 0.55,
            },
        }
    )


DEFAULT_MODE_PROFILES: Dict[str, Dict[str, Any]] = {
    name: dict(profile) for name, profile in SpeechRecognizerConfig().mode_profiles.items()
}


class SpeechServiceClient:
    """HTTP-Client fuer den Go-basierten speechtaskd-Service."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        token: Optional[str] = None,
        *,
        timeout: float = 6.0,
        logger: Optional[Logger] = None,
    ) -> None:
        env_disable = os.getenv("JARVIS_SPEECHD_ENABLED")
        disable_flag = env_disable is not None and env_disable.strip().lower() in {"0", "false", "no"}
        chosen_url = base_url or os.getenv("JARVIS_SPEECHD_URL") or "http://127.0.0.1:7074"
        if disable_flag:
            chosen_url = ""
        self.base_url = chosen_url.rstrip("/") if chosen_url else ""
        self.token = token or os.getenv("JARVIS_SPEECHD_TOKEN") or os.getenv("SPEECHD_TOKEN")
        self.timeout = timeout
        self.enabled = bool(self.base_url)
        self.logger = logger or Logger()
        self.session = requests.Session()

    @classmethod
    def from_settings(cls, settings: Optional[Any] = None, logger: Optional[Logger] = None) -> "SpeechServiceClient":
        base_url = None
        token = None
        timeout = 6.0
        try:
            raw = getattr(settings, "settings", {}) if settings else {}
            go_cfg = raw.get("go_services") or {}
            speech_cfg = go_cfg.get("speechtaskd", go_cfg) if isinstance(go_cfg, dict) else {}
            if isinstance(speech_cfg, dict):
                base_url = speech_cfg.get("base_url") or speech_cfg.get("url")
                token = speech_cfg.get("token") or speech_cfg.get("api_key")
                timeout = float(speech_cfg.get("timeout_seconds", timeout))
        except Exception:
            pass
        return cls(base_url=base_url, token=token, timeout=timeout, logger=logger)

    def recognize(self, raw_audio: bytes, sample_rate: int, channels: int) -> Optional[str]:
        if not self.enabled or not raw_audio:
            return None
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["X-API-Key"] = self.token
        payload = {
            "audio": base64.b64encode(raw_audio).decode("ascii"),
            "sample_rate": sample_rate,
            "channels": channels,
        }
        try:
            resp = self.session.post(f"{self.base_url}/speech/recognize", json=payload, headers=headers, timeout=self.timeout)
            if not resp.ok:
                return None
            data = resp.json() or {}
            text = data.get("transcript")
            if isinstance(text, str):
                return text
        except Exception as exc:
            self.logger.debug("speechtaskd recognize fehlgeschlagen: %s", exc)
        return None


class SpeechRecognizer:
    """Speech recognition with wake word and buffered command capture."""

    def __init__(
        self,
        wake_word_callback: Callable[[], None],
        command_callback: Callable[[str], None],
        *,
        config: Optional[SpeechRecognizerConfig] = None,
        settings: Optional[object] = None,
    ) -> None:
        self.logger = Logger()
        self.speechd_client = SpeechServiceClient.from_settings(settings, logger=self.logger)
        missing_deps: List[str] = []
        if pyaudio is None:
            missing_deps.append("pyaudio")
        if WhisperModel is None:
            missing_deps.append("faster_whisper")
        self._dependencies_available = not missing_deps
        if missing_deps:
            self.logger.warning(
                "Spracherkennung deaktiviert: fehlende Abhaengigkeiten (%s).",
                ", ".join(missing_deps),
            )
        self.wake_word_callback = wake_word_callback
        self.command_callback = command_callback

        self.config = config or self._build_config_from_settings(settings)
        self.sample_rate = self.config.sample_rate
        self.chunk_size = self.config.chunk_size
        self.channels = self.config.channels
        self.command_timeout = max(0.6, float(self.config.command_timeout))
        self._duplicate_filter = bool(self.config.duplicate_filter)
        self._wake_word_enabled = bool(getattr(self.config, "wake_word_enabled", True))
        if not self._wake_word_enabled:
            self.logger.warning("Wake-Word-Erkennung war deaktiviert; aktiviere sie aus Sicherheitsgruenden.")
            self._wake_word_enabled = True
            try:
                self.config.wake_word_enabled = True
            except Exception:
                pass

        self.wake_words = [word.lower().strip() for word in self.config.wake_words if word]
        if not self.wake_words and self._wake_word_enabled:
            self.wake_words = ["jarvis"]
        if self._wake_word_enabled and self.wake_words:
            pattern_parts = sorted({word for word in self.wake_words}, key=len, reverse=True)
            self._wake_word_pattern = re.compile("|".join(re.escape(word) for word in pattern_parts), re.IGNORECASE)
        else:
            self._wake_word_pattern = None

        # Recognition state
        self.is_listening = False
        self.is_recording = False

        # Audio
        self.audio: Optional[pyaudio.PyAudio] = None
        self.stream: Optional[pyaudio.Stream] = None

        # Command buffering
        self._buffer_lock = threading.Lock()
        self._command_buffer: List[str] = []
        self._capture_active = False
        self._flush_timer: Optional[threading.Timer] = None
        self._last_transcript: str = ""
        self._emotion_analyzer = EmotionAnalyzer()
        self._last_emotion_snapshot = None
        self._command_audio_segments: List[bytes] = []
        self._last_audio_blob: Optional[bytes] = None
        self._selected_input_name: Optional[str] = None
        self._recent_input_level: float = 0.0
        self._capture_started_at: Optional[float] = None
        self._noise_floor: float = 0.012
        self._noise_floor_decay: float = 0.96

        try:
            configured_silence = float(getattr(self.config, "silence_timeout", 0.7))
        except Exception:
            configured_silence = 0.65
        try:
            configured_max_duration = float(getattr(self.config, "max_command_duration", 3.8))
        except Exception:
            configured_max_duration = 3.8
        if configured_max_duration <= 0.0:
            configured_max_duration = 3.8
        self._capture_max_duration = max(2.0, min(4.0, configured_max_duration))
        self._silence_timeout = max(0.35, min(self._capture_max_duration, configured_silence or 0.7))

        # Modellverwaltung
        self._model_lock = threading.RLock()
        self._gpu_disabled = False
        self._fallback_in_progress = False
        self._active_device: Optional[str] = None
        self._active_compute: Optional[str] = None

        # Whisper / transcription
        self._whisper_model_name: str = (self.config.whisper_model or "distil-large-v3").strip()
        self._whisper_model: Optional[WhisperModel] = None
        self._pending_audio = bytearray()
        self._transcription_window = 2.4  # seconds
        self._transcription_min_bytes = int(self.sample_rate * self.channels * 2 * self._transcription_window)
        self._transcription_overlap_bytes = int(self.sample_rate * self.channels * 2 * 0.5)
        self._last_whisper_output: str = ""
        min_chunk_bytes = self.chunk_size * self.channels * 2
        if self._transcription_min_bytes < min_chunk_bytes:
            self._transcription_min_bytes = min_chunk_bytes
        self._whisper_downloader = WhisperDownloader()
        self._hotword_manager = HotwordManager(settings)
        self._fallback_language = (self.config.fallback_language or "de").strip() or "de"
        try:
            self._history_limit = max(200, int(self.config.max_history_chars))
        except Exception:
            self._history_limit = 1200
        self._mode_profiles = self._prepare_profiles(self.config.mode_profiles)
        self._inject_command_hotwords()
        self._default_mode = (self.config.default_mode or "command").strip().lower()
        if self._default_mode not in self._mode_profiles:
            self._default_mode = "command"
        self._current_mode = self._default_mode
        self._ignored_phrases = [phrase.lower() for phrase in (self.config.ignored_phrases or [])]
        self._command_aliases = {
            str(alias).lower(): str(replacement).lower()
            for alias, replacement in (self.config.command_aliases or {}).items()
            if str(alias).strip() and str(replacement).strip()
        }
        self._profile_state: Dict[str, Dict[str, Any]] = {
            name: {"previous_text": ""} for name in self._mode_profiles
        }
        self._preferred_model_id = self.config.model_id
        self._model_load_strategy: str = 'startup'
        if settings and hasattr(settings, 'get_model_load_strategy'):
            try:
                strategy = settings.get_model_load_strategy('whisper', default='startup', model_type='stt')
                if strategy in ('startup', 'on_demand'):
                    self._model_load_strategy = strategy
            except Exception:
                pass
        self._model_enabled: bool = True
        self._model_disabled_notified: bool = False
        if settings and hasattr(settings, 'is_model_enabled'):
            try:
                self._model_enabled = bool(settings.is_model_enabled('whisper', default=True, model_type='stt'))
            except Exception:
                self._model_enabled = True
        if not self._dependencies_available:
            self._model_enabled = False

        self.setup_audio()
        if self._model_enabled:
            if self._model_load_strategy == 'startup':
                self.load_model()
            else:
                self.logger.info("Whisper-Modell wird On-Demand initialisiert.")
        else:
            self.logger.info("Whisper-Spracherkennung ist deaktiviert; Modelle werden nicht geladen.")

    # ------------------------------------------------------------------
    # Configuration helpers
    # ------------------------------------------------------------------
    def _mode_key(self, name: Optional[str]) -> str:
        return str(name or "").strip().lower()

    def _prepare_profiles(self, profiles: Optional[Dict[str, Dict[str, Any]]]) -> Dict[str, Dict[str, Any]]:
        """Merge default and user-defined profiles with sanitised options."""
        prepared: Dict[str, Dict[str, Any]] = {}

        def _clone_profile(source: Dict[str, Any], label: str) -> Dict[str, Any]:
            meta: Dict[str, Any] = {}
            profile: Dict[str, Any] = {"__label__": label}
            for key, value in (source or {}).items():
                if key in PROFILE_META_KEYS:
                    if value is None:
                        continue
                    if key == "max_history_chars":
                        try:
                            limit = int(value)
                        except Exception:
                            continue
                        if limit > 0:
                            meta[key] = limit
                    continue
                if key not in WHISPER_TRANSCRIBE_OPTIONS:
                    continue
                if value is None:
                    continue
                if key == "vad_parameters":
                    if isinstance(value, dict):
                        filtered = {k: v for k, v in value.items() if v is not None}
                        if filtered:
                            profile[key] = filtered
                    continue
                profile[key] = value
            if meta:
                profile["_meta"] = meta
            return profile

        for default_name, default_profile in DEFAULT_MODE_PROFILES.items():
            key = self._mode_key(default_name)
            prepared[key] = _clone_profile(default_profile, default_name)

        if profiles:
            for name, overrides in profiles.items():
                key = self._mode_key(name)
                if not key:
                    continue
                base = prepared.get(key, _clone_profile({}, name or key))
                merged = copy.deepcopy(base)
                override_clone = _clone_profile(overrides or {}, name or key)
                for option, value in override_clone.items():
                    if option in ("__label__", "_meta"):
                        continue
                    merged[option] = value
                if "_meta" in override_clone:
                    existing_meta = dict(merged.get("_meta") or {})
                    existing_meta.update(override_clone["_meta"])
                    merged["_meta"] = existing_meta
                # Preserve human readable label
                merged["__label__"] = override_clone.get("__label__", base.get("__label__", name or key))
                prepared[key] = merged

        # Ensure every profile has a language fallback
        for name, profile in prepared.items():
            if not profile.get("language"):
                profile["language"] = self._fallback_language
        return prepared

    def _inject_command_hotwords(self) -> None:
        """Augment the command profile with dynamic hotwords and prompt examples."""
        manager = getattr(self, "_hotword_manager", None)
        if not manager:
            return
        command_profile = self._mode_profiles.get("command")
        if not command_profile:
            return
        merged_hotwords = manager.merge_hotwords(command_profile.get("hotwords"))
        custom_hotwords = [
            word.strip().lower() for word in (self.config.command_hotwords or []) if isinstance(word, str) and word.strip()
        ]
        if custom_hotwords:
            merged_hotwords = sorted({*merged_hotwords, *custom_hotwords})
        if merged_hotwords:
            command_profile["hotwords"] = " | ".join(merged_hotwords[:80])
            command_profile["initial_prompt"] = manager.build_initial_prompt(
                command_profile.get("initial_prompt", ""),
                merged_hotwords,
            )

    def _normalize_model_alias(self, alias: str) -> str:
        """Normalise a whisper model alias for logging and caches."""
        value = str(alias or "").strip()
        value = value.replace("\\", "/")
        if "/" in value:
            value = value.split("/")[-1]
        if value.endswith(".bin") or value.endswith(".pt"):
            value = value.rsplit(".", 1)[0]
        return value

    def available_modes(self) -> List[str]:
        """Return the list of known recognition modes (machine-friendly keys)."""
        return list(self._mode_profiles.keys())

    def get_mode(self, *, human_readable: bool = False) -> str:
        """Return the current recognition mode."""
        if human_readable:
            profile = self._mode_profiles.get(self._current_mode, {})
            label = profile.get("__label__") or self._current_mode
            return str(label)
        return self._current_mode

    def set_mode(self, mode_name: str) -> bool:
        """Switch to a different recognition profile."""
        key = self._mode_key(mode_name)
        if not key or key not in self._mode_profiles:
            self.logger.warning(f"Unbekannter Erkennungsmodus '{mode_name}'")
            return False
        if key == self._current_mode:
            return True
        self.logger.info(f"Wechsle Spracherkennungsmodus zu '{self._mode_profiles[key].get('__label__', key)}'")
        self._current_mode = key
        return True

    def reset_mode_history(self, mode_name: Optional[str] = None) -> None:
        """Clear accumulated history for one or all recognition modes."""
        if mode_name is None:
            for state in self._profile_state.values():
                state["previous_text"] = ""
                state.pop("last_update", None)
            return
        key = self._mode_key(mode_name)
        state = self._profile_state.get(key)
        if state is not None:
            state["previous_text"] = ""
            state.pop("last_update", None)

    def _build_config_from_settings(self, settings: Optional[object]) -> SpeechRecognizerConfig:
        config = SpeechRecognizerConfig()
        if not settings:
            return config
        try:
            speech = settings.get('speech', {})  # type: ignore[attr-defined]
            audio = settings.get('audio', {})    # type: ignore[attr-defined]
            stt_cfg = settings.get('stt', {})    # type: ignore[attr-defined]
        except Exception:
            speech = {}
            audio = {}
            stt_cfg = {}
        if isinstance(audio, dict):
            config.sample_rate = int(audio.get('sample_rate', config.sample_rate))
            config.chunk_size = int(audio.get('chunk_size', config.chunk_size))
            config.channels = int(audio.get('channels', config.channels))
            # Eingabegerät: Name oder Index
            try:
                name = audio.get('input_device')
                if isinstance(name, str) and name.strip():
                    config.input_device = name.strip()
            except Exception:
                pass
            try:
                idx = audio.get('input_device_index')
                if isinstance(idx, int):
                    config.input_device_index = idx
            except Exception:
                pass
            try:
                preferred = audio.get('preferred_input_substrings')
                if isinstance(preferred, (list, tuple)):
                    config.preferred_input_keywords = [str(entry).strip() for entry in preferred if entry]
            except Exception:
                pass
        if isinstance(speech, dict):
            wake_words = speech.get('wake_words')
            if isinstance(wake_words, Sequence) and wake_words:
                config.wake_words = [str(word) for word in wake_words if word]
            if 'wake_word_enabled' in speech:
                config.wake_word_enabled = bool(speech.get('wake_word_enabled'))
            language_value = speech.get('language')
            if isinstance(language_value, str) and language_value.strip():
                lang = language_value.strip()
                config.fallback_language = lang.split("-")[0].strip() or lang
            custom_hotwords = speech.get('command_hotwords')
            if isinstance(custom_hotwords, (list, tuple)):
                config.command_hotwords = [str(word).strip() for word in custom_hotwords if isinstance(word, str) and word.strip()]
            aliases = speech.get('command_aliases')
            if isinstance(aliases, dict):
                alias_map: Dict[str, str] = {}
                for key, value in aliases.items():
                    if not isinstance(key, str) or not isinstance(value, str):
                        continue
                    alias_key = key.strip().lower()
                    alias_value = value.strip().lower()
                    if alias_key and alias_value:
                        alias_map[alias_key] = alias_value
                if alias_map:
                    config.command_aliases.update(alias_map)
            ignored = speech.get('ignored_phrases')
            if isinstance(ignored, (list, tuple)):
                filtered = [str(item).strip().lower() for item in ignored if isinstance(item, str) and item.strip()]
                if filtered:
                    config.ignored_phrases = filtered
            recognition = speech.get('recognition', {})
            if isinstance(recognition, dict):
                timeout = recognition.get('command_timeout')
                if timeout is not None:
                    try:
                        config.command_timeout = float(timeout)
                    except (TypeError, ValueError):
                        pass
                silence_timeout = recognition.get('silence_timeout')
                if silence_timeout is not None:
                    try:
                        config.silence_timeout = float(silence_timeout)
                    except (TypeError, ValueError):
                        pass
                max_duration = recognition.get('max_command_duration')
                if max_duration is not None:
                    try:
                        config.max_command_duration = float(max_duration)
                    except (TypeError, ValueError):
                        pass
            model_value = speech.get('whisper_model') or speech.get('vosk_model')
            if isinstance(model_value, str) and model_value.strip():
                config.whisper_model = model_value.strip()
        if isinstance(stt_cfg, dict):
            model_id = stt_cfg.get("model")
            if isinstance(model_id, str) and model_id.strip():
                config.model_id = model_id.strip()
                base_alias = model_id.split("/")[-1]
                base_alias = base_alias.replace("faster-whisper-", "")
                base_alias = base_alias.replace("distil-whisper-", "")
                config.whisper_model = base_alias or config.whisper_model
            device = stt_cfg.get("device")
            if isinstance(device, str) and device.strip():
                config.device = device.strip().lower()
            compute_type = stt_cfg.get("compute_type")
            if isinstance(compute_type, str) and compute_type.strip():
                config.compute_type = compute_type.strip()
            default_mode = stt_cfg.get("default_mode")
            if isinstance(default_mode, str) and default_mode.strip():
                config.default_mode = default_mode.strip()
            fallback_language = stt_cfg.get("language") or stt_cfg.get("fallback_language")
            if isinstance(fallback_language, str) and fallback_language.strip():
                lang = fallback_language.strip()
                config.fallback_language = lang.split("-")[0].strip() or lang
            history_limit = stt_cfg.get("max_history_chars")
            if history_limit is not None:
                try:
                    config.max_history_chars = int(history_limit)
                except (TypeError, ValueError):
                    pass
            profiles = stt_cfg.get("mode_profiles")
            if isinstance(profiles, dict):
                config.mode_profiles = profiles
        return config

    # ------------------------------------------------------------------
    # Audio / model initialisation
    # ------------------------------------------------------------------
    def setup_audio(self) -> None:
        """Initialise the audio interface."""
        if pyaudio is None:
            self.logger.warning("PyAudio nicht verfuegbar; Mikrofonaufnahme ist deaktiviert.")
            self.audio = None
            return
        try:
            self.audio = pyaudio.PyAudio()
            self.logger.info("Audio-System initialisiert")
        except Exception as exc:
            self.logger.error(f"Fehler bei Audio-Initialisierung: {exc}")
            self.audio = None

    def load_model(self, *, force_device: Optional[str] = None, force_compute: Optional[str] = None) -> bool:
        """Initialise the Whisper model with fallbacks."""
        with self._model_lock:
            if not self._dependencies_available or WhisperModel is None:
                self.logger.warning("Whisper STT kann nicht geladen werden: fehlende faster_whisper-Installation.")
                self._model_enabled = False
                return False
            if not self._model_enabled:
                if not self._model_disabled_notified:
                    self.logger.info("Whisper-Modell ist deaktiviert; kein Ladevorgang.")
                    self._model_disabled_notified = True
                self._whisper_model = None
                self._active_device = None
                self._active_compute = None
                return False
            alias_candidates: List[str] = []
            if self._preferred_model_id:
                alias_candidates.append(self._preferred_model_id)
            if self._whisper_model_name:
                alias_candidates.append(self._whisper_model_name)
            for fallback in ("large-v3", "medium", "small", "distil-small.en"):
                if fallback.lower() not in {alias.lower() for alias in alias_candidates}:
                    alias_candidates.append(fallback)

            normalized_aliases: List[str] = []
            seen_alias: set[str] = set()
            for alias in alias_candidates:
                key = alias.lower()
                if key not in seen_alias:
                    seen_alias.add(key)
                    normalized_aliases.append(alias)

            def _normalise_device(device_name: str) -> str:
                return (device_name or "").strip().lower()

            device_candidates: List[Tuple[str, str]] = []
            if force_device:
                forced_device = _normalise_device(force_device)
                if forced_device:
                    compute_candidate = force_compute or ("int8" if forced_device == "cpu" else getattr(self.config, "compute_type", None))
                    forced_compute = str(compute_candidate or ("int8" if forced_device == "cpu" else "float32")).strip()
                    if not forced_compute:
                        forced_compute = "int8" if forced_device == "cpu" else "float32"
                    device_candidates.append((forced_device, forced_compute))
            else:
                try:
                    if not self._gpu_disabled:
                        device_candidates.append(self._select_device())
                except Exception as exc:
                    self.logger.debug(f"Geraeteauswahl fuer Whisper fehlgeschlagen: {exc}")
                if ("cpu", "int8") not in device_candidates:
                    device_candidates.append(("cpu", "int8"))

            def _compute_sequence(device: str, compute: str) -> List[str]:
                device_norm = (device or "").strip().lower()
                compute_norm = (compute or "").strip()
                if not compute_norm:
                    compute_norm = "int8" if device_norm == "cpu" else "float16"

                candidates: List[str] = []

                def push(option: str) -> None:
                    opt = (option or "").strip()
                    if opt:
                        candidates.append(opt)

                if device_norm in ("cuda", "gpu", "mps"):
                    push("float16")
                    push(compute_norm)
                    if device_norm in ("cuda", "gpu"):
                        push("int8_float16")
                    push("float32")
                else:
                    push(compute_norm)
                    push("int8")
                    push("float32")
                    push("float16")

                ordered: List[str] = []
                seen_local: set[str] = set()
                for entry in candidates:
                    if entry not in seen_local:
                        seen_local.add(entry)
                        ordered.append(entry)
                return ordered

            last_error: Optional[Exception] = None
            for alias in normalized_aliases:
                for device, compute_type in device_candidates:
                    for compute_choice in _compute_sequence(device, compute_type):
                        try:
                            local_dir = self._whisper_downloader.ensure_model(alias)
                        except Exception as exc:
                            last_error = exc
                            self.logger.warning(
                                f"Whisper-Modell '{alias}' konnte nicht heruntergeladen werden: {exc}"
                            )
                            continue

                        try:
                            self.logger.info(
                                f"Lade Whisper-Modell '{alias}' (Device={device}, Compute={compute_choice})"
                            )
                            self._whisper_model = WhisperModel(
                                str(local_dir),
                                device=device,
                                compute_type=compute_choice,
                            )
                            self._whisper_model_name = self._normalize_model_alias(alias)
                            self._active_device = device
                            self._active_compute = compute_choice
                            if device != "cpu":
                                self._gpu_disabled = False
                            return True
                        except Exception as exc:
                            last_error = exc
                            self.logger.warning(
                                f"Whisper-Modell '{alias}' konnte nicht geladen werden: {exc}"
                            )
                            continue

            self._whisper_model = None
            self._active_device = None
            self._active_compute = None
            if last_error:
                self.logger.error(f"Whisper-Modell konnte nicht geladen werden: {last_error}")
            return False
    def _select_device(self) -> Tuple[str, str]:
        """Bestimmt das passende Ausfuehrungsgeraet fuer Whisper."""
        preferred_device = (self.config.device or "cpu").lower()
        preferred_compute = self.config.compute_type or "int8"

        def _fallback_compute(device_choice: str) -> str:
            if device_choice == "cpu" and preferred_compute.startswith("int8"):
                return "int8"
            return preferred_compute

        if torch is not None:
            try:
                if preferred_device in ("cuda", "gpu"):
                    if torch.cuda.is_available():
                        return "cuda", preferred_compute
                    self.logger.warning("CUDA nicht verfuegbar – falle auf CPU zurueck")
                elif preferred_device in ("mps", "metal", "apple"):
                    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                        return "mps", preferred_compute
                    self.logger.warning("MPS nicht verfuegbar – falle auf CPU zurueck")
            except Exception as exc:
                self.logger.debug(f"GPU-Abfrage fehlgeschlagen: {exc}")

            try:
                if torch.cuda.is_available():
                    return "cuda", preferred_compute
                if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                    return "mps", preferred_compute
            except Exception as exc:
                self.logger.debug(f"Automatische Geraeteauswahl fehlgeschlagen: {exc}")

        return "cpu", _fallback_compute("cpu")

    def _should_trigger_gpu_fallback(self, exc: Exception) -> bool:
        """Check whether an exception warrants disabling GPU usage."""
        message = str(exc or "").lower()
        if not message:
            return False
        keywords = (
            "cublas",
            "cuda",
            "cudnn",
            "not supported",
            "illegal memory access",
            "device-side assert",
        )
        return any(token in message for token in keywords)

    def _fallback_to_cpu(self) -> bool:
        """Reload the whisper model on CPU after a GPU failure."""
        if self._active_device == "cpu" or self._fallback_in_progress:
            return False
        self._fallback_in_progress = True
        try:
            self._gpu_disabled = True
            self.logger.warning("GPU-Whisper-Fehler erkannt - wechsle dauerhaft auf CPU-Betrieb.")
            success = self.load_model(force_device="cpu", force_compute="int8")
            if success:
                self.logger.info("Whisper-Modell erfolgreich auf CPU neu geladen.")
            else:
                self.logger.error("CPU-Fallback fuer Whisper ist fehlgeschlagen.")
            return success
        finally:
            self._fallback_in_progress = False

    def check_model(self) -> bool:
        """Return True if a recognition model ist verfuegbar oder lokal vorliegt."""
        if not self._model_enabled:
            return False
        if self._whisper_model is not None:
            return True
        if self._model_load_strategy == 'on_demand' and self._whisper_downloader:
            alias = self._preferred_model_id or self.config.model_id or self.config.whisper_model
            alias = alias or "large-v3"
            try:
                return self._whisper_downloader.has_model(alias)
            except Exception:
                return False
        return False

    def _ensure_model_ready(self) -> bool:
        """Laedt das Whisper-Modell falls erforderlich."""
        if not self._dependencies_available:
            return False
        if not self._model_enabled:
            return False
        if self._whisper_model is not None:
            return True
        if self._model_load_strategy == 'on_demand':
            self.logger.info("Lade Whisper-Modell (On-Demand)...")
            return self.load_model()
        return False

    def is_enabled(self) -> bool:
        """Gibt zurueck, ob die Spracherkennung lauffaehig ist."""
        return bool(self._dependencies_available and self._model_enabled)

    def list_available_models(self) -> Dict[str, Dict[str, Any]]:
        """Gibt eine Uebersicht verfuegbarer STT-Modelle zurueck."""
        alias_raw = self._preferred_model_id or self.config.model_id or self.config.whisper_model or "large-v3"
        alias_display = self._normalize_model_alias(alias_raw)
        exists = False
        if self._whisper_downloader:
            try:
                exists = self._whisper_downloader.has_model(alias_raw)
            except Exception:
                exists = False
        return {
            "whisper": {
                "display_name": f"Whisper ({alias_display})",
                "description": "Faster-Whisper fuer deutschsprachige Echtzeit-Spracherkennung.",
                "exists": exists,
                "loaded": self._whisper_model is not None,
                "enabled": self._model_enabled,
                "default_strategy": "startup",
            }
        }

    def test_microphone(self) -> bool:
        """Check whether an input device is available."""
        try:
            if not self.audio:
                return False
            info = self.audio.get_host_api_info_by_index(0)
            for index in range(info.get('deviceCount', 0)):
                device = self.audio.get_device_info_by_host_api_device_index(0, index)
                if device.get('maxInputChannels', 0) > 0:
                    self.logger.info(f"Mikrofon gefunden: {device.get('name')}")
                    return True
            return False
        except Exception as exc:
            self.logger.error(f"Fehler beim Mikrofon-Test: {exc}")
            return False

    # ------------------------------------------------------------------
    # Runtime
    # ------------------------------------------------------------------
    def start_listening(self) -> None:
        """Start continuous listening in the current thread."""
        if not self._dependencies_available:
            self.logger.info("Spracherkennung nicht verfuegbar (fehlende Abhaengigkeiten).")
            self.is_listening = False
            return
        if not self._model_enabled:
            self.logger.info("Spracherkennung ist deaktiviert; Start wird uebersprungen.")
            self.is_listening = False
            return
        if not self._ensure_model_ready():
            self.logger.error("Kein Sprachmodell verfuegbar")
            self.is_listening = False
            return
        if not self.audio:
            self.logger.error("Audio-System nicht initialisiert")
            self.is_listening = False
            return

        self.is_listening = True
        self.logger.info("Spracherkennung gestartet")
        self._pending_audio = bytearray()
        self._last_whisper_output = ""

        try:
            input_index = self._resolve_input_device_index()
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
                input_device_index=input_index if input_index is not None else None,
            )
            selected_name = self._selected_input_name or 'Standard'
            if input_index is not None:
                self.logger.info(f'Eingabegeraet gewaehlt: {selected_name} (Index {input_index})')
            else:
                self.logger.info(f'Eingabegeraet gewaehlt: {selected_name}')
        except Exception as exc:
            self.logger.error(f"Fehler beim Starten des Audio-Streams: {exc}")
            self.is_listening = False
            return

        try:
            while self.is_listening and self.stream:
                try:
                    data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                except Exception as exc:
                    self.logger.error(f"Audio-Lesefehler: {exc}")
                    time.sleep(0.1)
                    continue
                self._recent_input_level = self._compute_level_from_bytes(data)
                try:
                    self._emotion_analyzer.update(data)
                except Exception as exc:
                    self.logger.debug(f"Emotionanalyse fehlgeschlagen: {exc}")
                if self._capture_active:
                    try:
                        self._command_audio_segments.append(bytes(data))
                    except Exception:
                        pass
                try:
                    self._handle_audio_chunk(data)
                except Exception as exc:
                    self.logger.error(f"Fehler bei Spracherkennung: {exc}")
        finally:
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
            self._cancel_flush_timer()
            self._reset_command_buffer(discard=True)
            self.is_listening = False
            self.is_recording = False

    def stop_listening(self) -> None:
        """Stop listening and release resources."""
        self.is_listening = False
        self.is_recording = False
        self._cancel_flush_timer()
        self._reset_command_buffer(discard=True)
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except Exception:
                pass
            self.stream = None
        self.logger.info("Spracherkennung gestoppt")
        self._recent_input_level = 0.0
        self._pending_audio = bytearray()
        self._last_whisper_output = ""

    # ------------------------------------------------------------------
    # Speech processing
    # ------------------------------------------------------------------
    def process_speech(self, text: str) -> None:
        """Process recognised text fragments."""
        fragment = self._clean_transcript((text or "").strip())
        if not fragment:
            return
        normalized = fragment.lower()
        if self._duplicate_filter and normalized == self._last_transcript:
            return
        self._last_transcript = normalized

        if not self._wake_word_enabled:
            if not self._capture_active:
                self.wake_word_callback()
                self._begin_command_capture(fragment)
            else:
                self._append_command_text(fragment)
            return

        if self._contains_wake_word(fragment):
            trimmed = self._strip_wake_words(fragment)
            self._reset_command_buffer(discard=True)
            self.wake_word_callback()
            self._begin_command_capture(trimmed)
            return

        if self._capture_active:
            self._append_command_text(fragment)

    def process_single_command(self, audio_data: bytes) -> str:
        """Process a single chunk of audio and return the transcript."""
        try:
            return self._transcribe_audio(audio_data)
        except Exception as exc:
            self.logger.error(f"Fehler bei Einzelbefehl-Verarbeitung: {exc}")
        return ""

    # ------------------------------------------------------------------
    # Command buffering helpers
    # ------------------------------------------------------------------
    def _begin_command_capture(self, initial_segment: str) -> None:
        self._cancel_flush_timer()
        with self._buffer_lock:
            self._command_buffer = []
            self._capture_active = True
            self.is_recording = True
            if initial_segment:
                cleaned = self._clean_transcript(initial_segment)
                if cleaned:
                    self._command_buffer.append(cleaned)
        self._emotion_analyzer.reset()
        self._last_emotion_snapshot = None
        self._command_audio_segments = []
        self._capture_started_at = time.monotonic()
        self._schedule_flush()

    def _append_command_text(self, segment: str) -> None:
        cleaned = self._clean_transcript(segment)
        if not cleaned:
            return
        with self._buffer_lock:
            if self._capture_active:
                if self._command_buffer:
                    last = self._command_buffer[-1]
                    if cleaned == last:
                        return
                    if last and cleaned.startswith(last) and len(cleaned) - len(last) <= 4:
                        self._command_buffer[-1] = cleaned
                    elif last and last.startswith(cleaned) and len(last) - len(cleaned) <= 4:
                        return
                    else:
                        self._command_buffer.append(cleaned)
                else:
                    self._command_buffer.append(cleaned)
        self._schedule_flush()

    def _schedule_flush(self) -> None:
        now = time.monotonic()
        remaining = None
        if self._capture_started_at is not None:
            remaining = self._capture_max_duration - (now - self._capture_started_at)
        immediate_flush = remaining is not None and remaining <= 0.15
        timeout = self._silence_timeout
        if remaining is not None and not immediate_flush:
            timeout = min(timeout, remaining)
        timeout = max(0.3, timeout)

        timer: Optional[threading.Timer] = None
        with self._buffer_lock:
            existing = self._flush_timer
            self._flush_timer = None
            if existing:
                try:
                    existing.cancel()
                except Exception:
                    pass
            if not immediate_flush:
                timer = threading.Timer(timeout, self._flush_command)
                timer.daemon = True
                self._flush_timer = timer

        if timer:
            timer.start()
        elif immediate_flush:
            self._flush_command()

    def _cancel_flush_timer(self) -> None:
        with self._buffer_lock:
            timer = self._flush_timer
            self._flush_timer = None
        if timer:
            try:
                timer.cancel()
            except Exception:
                pass

    def _flush_command(self) -> None:
        with self._buffer_lock:
            timer = self._flush_timer
            self._flush_timer = None
        if timer:
            try:
                timer.cancel()
            except Exception:
                pass

        with self._buffer_lock:
            if not self._capture_active:
                return
            command_text = ' '.join(self._command_buffer).strip()
            self._command_buffer = []
            self._capture_active = False
            self.is_recording = False
            self._capture_started_at = None

        if not command_text:
            if self._wake_word_enabled:
                self.logger.info("Timeout: Kein Befehl nach Wake-Word erkannt")
            else:
                self.logger.info("Timeout: Keine Sprache erkannt")
            return
        try:
            self._last_emotion_snapshot = self._emotion_analyzer.finalize().as_dict()
        except Exception as exc:
            self.logger.debug(f"Emotionsergebnis konnte nicht ermittelt werden: {exc}")
            self._last_emotion_snapshot = {"label": "neutral", "confidence": 0.0}
        try:
            audio_blob = b''.join(self._command_audio_segments)
            self._last_audio_blob = audio_blob if audio_blob else None
        except Exception:
            self._last_audio_blob = None
        finally:
            self._command_audio_segments = []
        try:
            self.command_callback(command_text)
        except Exception as exc:
            self.logger.error(f"Fehler beim Ausloesen des Befehls: {exc}")

    def _reset_command_buffer(self, *, discard: bool) -> None:
        with self._buffer_lock:
            self._command_buffer = []
            if discard:
                self._capture_active = False
                self.is_recording = False
        if discard:
            self._capture_started_at = None
            self._emotion_analyzer.reset()
            self._command_audio_segments = []
            self._last_audio_blob = None

    # ------------------------------------------------------------------
    # Wake word helpers
    # ------------------------------------------------------------------
    def _contains_wake_word(self, text: str) -> bool:
        if not text or not self._wake_word_enabled or not self._wake_word_pattern:
            return False
        return bool(self._wake_word_pattern.search(text))

    def _strip_wake_words(self, text: str) -> str:
        if not text:
            return ''
        if not self._wake_word_enabled or not self._wake_word_pattern:
            return text.strip()
        stripped = self._wake_word_pattern.sub(' ', text)
        return re.sub(r'\s+', ' ', stripped).strip()

    # ------------------------------------------------------------------
    # Device helpers
    # ------------------------------------------------------------------
    def _resolve_input_device_index(self) -> Optional[int]:
        """Find an appropriate input device index using settings and heuristics."""
        self._selected_input_name = None
        if not self.audio:
            return None

        devices: List[Dict[str, Any]] = []
        try:
            host_info = self.audio.get_host_api_info_by_index(0)
            for i in range(host_info.get('deviceCount', 0)):
                try:
                    dev = self.audio.get_device_info_by_host_api_device_index(0, i)
                except Exception:
                    continue
                if dev.get('maxInputChannels', 0) > 0:
                    devices.append(dev)
        except Exception as exc:
            self.logger.error(f"Eingabegeraete konnten nicht ermittelt werden: {exc}")
            return None

        if not devices:
            return None

        desired = (self.config.input_device or '').strip().lower() if isinstance(self.config.input_device, str) else ''
        if desired:
            for dev in devices:
                dev_name = str(dev.get('name', ''))
                name_lower = dev_name.lower()
                if desired == name_lower or desired in name_lower:
                    self._selected_input_name = dev_name
                    self.logger.info(f"Eingabegeraet gewaehlt (Name): {dev_name} (Index {dev.get('index')})")
                    return int(dev.get('index'))

        if isinstance(self.config.input_device_index, int):
            for dev in devices:
                if int(dev.get('index')) == int(self.config.input_device_index):
                    self._selected_input_name = dev.get('name')
                    self.logger.info(
                        f"Eingabegeraet gewaehlt (Index): {self._selected_input_name} (Index {self.config.input_device_index})"
                    )
                    return int(self.config.input_device_index)
            try:
                dev = self.audio.get_device_info_by_host_api_device_index(0, int(self.config.input_device_index))
                if dev and dev.get('maxInputChannels', 0) > 0:
                    self._selected_input_name = dev.get('name')
                    self.logger.info(
                        f"Eingabegeraet gewaehlt (Index): {self._selected_input_name} (Index {self.config.input_device_index})"
                    )
                    return int(self.config.input_device_index)
            except Exception:
                pass

        preferred = [kw.lower() for kw in (self.config.preferred_input_keywords or []) if isinstance(kw, str) and kw]
        if not preferred:
            preferred = ['jbl', 'headset', 'wireless', 'chat', 'microphone', 'mic']
        penalty_keywords = ('array', 'loopback', 'speaker', 'stereo', 'mix', 'pico')

        best_device: Optional[Dict[str, Any]] = None
        best_score = float('-inf')
        for dev in devices:
            name_value = str(dev.get('name', ''))
            lname = name_value.lower()
            score = 0.0
            for kw in preferred:
                if kw in lname:
                    score += 2.0
            for bad in penalty_keywords:
                if bad in lname:
                    score -= 1.5
            if 'default' in lname or 'standard' in lname:
                score += 0.5
            if score > best_score:
                best_device = dev
                best_score = score

        if best_device and best_score > -0.5:
            idx = int(best_device.get('index'))
            self._selected_input_name = best_device.get('name')
            self.logger.info(f"Eingabegeraet gewaehlt (Heuristik): {self._selected_input_name} (Index {idx})")
            return idx

        fallback = devices[0]
        self._selected_input_name = fallback.get('name')
        idx = int(fallback.get('index'))
        self.logger.info(f"Eingabegeraet gewaehlt (Fallback): {self._selected_input_name} (Index {idx})")
        return idx

    def _collect_input_devices(self) -> List[Dict[str, Any]]:
        if not self.audio:
            return []
        devices: List[Dict[str, Any]] = []
        try:
            host_info = self.audio.get_host_api_info_by_index(0)
            for i in range(host_info.get('deviceCount', 0)):
                try:
                    dev = self.audio.get_device_info_by_host_api_device_index(0, i)
                except Exception:
                    continue
                if dev.get('maxInputChannels', 0) > 0:
                    idx = int(dev.get('index', i))
                    name = str(dev.get('name', ''))
                    devices.append({'index': idx, 'name': name})
        except Exception as exc:
            self.logger.error(f"Eingabegeraete konnten nicht ermittelt werden: {exc}")
        self._available_devices = devices
        return list(devices)

    def enumerate_input_devices(self) -> List[Dict[str, Any]]:
        return list(self._collect_input_devices())

    def get_available_devices(self) -> List[Dict[str, Any]]:
        return list(self._available_devices)

    def apply_audio_preferences(
        self,
        *,
        device_name: Optional[str] = None,
        device_index: Optional[int] = None,
        preferred_keywords: Optional[List[str]] = None,
    ) -> None:
        if device_name is not None:
            self.config.input_device = device_name.strip() if device_name else None
        if device_index is not None:
            self.config.input_device_index = int(device_index)
        if preferred_keywords is not None:
            self.config.preferred_input_keywords = [kw for kw in preferred_keywords if kw]
        self._selected_input_name = None
        self._pending_audio = bytearray()
        self._last_whisper_output = ""
        self._recent_input_level = 0.0

    def get_input_level(self) -> float:
        """Returns the most recently observed input level (0.0-1.0)."""
        return max(0.0, min(1.0, float(self._recent_input_level)))

    def sample_input_level(self, duration: float = 1.0) -> Optional[float]:
        """Active measurement of the input level over a short duration."""
        duration = float(duration or 0.0)
        if duration <= 0.0:
            duration = 1.0
        if not self.audio:
            self.setup_audio()
        if not self.audio:
            return None

        chunk = max(512, min(self.chunk_size, 2048))
        frames_needed = max(1, int((duration * self.sample_rate) / chunk))

        input_index = None
        try:
            input_index = self._resolve_input_device_index()
        except Exception:
            input_index = None

        stream = None
        levels: List[float] = []
        try:
            stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=chunk,
                input_device_index=input_index if input_index is not None else None,
            )
            for _ in range(frames_needed):
                try:
                    data = stream.read(chunk, exception_on_overflow=False)
                except Exception as exc:
                    self.logger.error(f"Audio-Lesefehler beim Mikrofon-Test: {exc}")
                    break
                level = self._compute_level_from_bytes(data)
                levels.append(level)
        except Exception as exc:
            self.logger.error(f"Mikrofon-Test fehlgeschlagen: {exc}")
            return None
        finally:
            if stream:
                try:
                    stream.stop_stream()
                    stream.close()
                except Exception:
                    pass

        if not levels:
            return 0.0
        averaged = sum(levels) / len(levels)
        return max(0.0, min(1.0, averaged))

    def _compute_level_from_bytes(self, data: bytes) -> float:
        """Berechnet einen normierten RMS-Pegel aus Roh-Audiodaten."""
        if not data:
            return 0.0
        try:
            samples = array('h')
            samples.frombytes(data)
            if not samples:
                return 0.0
            sum_squares = 0.0
            for sample in samples:
                sum_squares += float(sample) * float(sample)
            rms = math.sqrt(sum_squares / len(samples)) if samples else 0.0
            if not rms:
                return 0.0
            normalized = rms / 32768.0
            return max(0.0, min(1.0, normalized))
        except Exception:
            return 0.0

    def _resolve_active_profile(self) -> Tuple[str, Dict[str, Any]]:
        """Return the active mode key and its profile dictionary."""
        profile = self._mode_profiles.get(self._current_mode)
        if profile is not None:
            return self._current_mode, profile
        if self._mode_profiles:
            key, prof = next(iter(self._mode_profiles.items()))
            return key, prof
        return "command", {}

    def _build_transcribe_options(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Compose whisper transcription kwargs and meta data for the current mode."""
        mode_key, profile = self._resolve_active_profile()
        options: Dict[str, Any] = {}
        meta = dict(profile.get("_meta") or {})
        base_prompt = str(profile.get("initial_prompt") or "").strip()

        for key, value in profile.items():
            if key in ("__label__", "_meta"):
                continue
            if key not in WHISPER_TRANSCRIBE_OPTIONS:
                continue
            if value is None:
                continue
            if key == "vad_parameters":
                if isinstance(value, dict):
                    filtered = {k: v for k, v in value.items() if v is not None}
                    if filtered:
                        options[key] = filtered
                continue
            options[key] = value

        if not options.get("language"):
            options["language"] = self._fallback_language

        state = self._profile_state.setdefault(mode_key, {"previous_text": ""})
        history = str(state.get("previous_text") or "").strip()
        history_limit = meta.get("max_history_chars") or self._history_limit
        if history_limit and history_limit > 0 and history and len(history) > history_limit:
            history = history[-history_limit:]

        prompt_parts: List[str] = []
        if base_prompt:
            prompt_parts.append(base_prompt)
        if history:
            include_history = bool(options.get("condition_on_previous_text", False))
            if include_history or not base_prompt:
                prompt_parts.append(history)
        if prompt_parts:
            combined_prompt = " ".join(part for part in prompt_parts if part).strip()
            if combined_prompt:
                options["initial_prompt"] = combined_prompt

        if mode_key == "command":
            options["beam_size"] = 1
            options["best_of"] = 1
            options["temperature"] = 0.0
            options["condition_on_previous_text"] = False
            options["language"] = options.get("language") or self._fallback_language
            options["vad_filter"] = True
            vad_params = options.get("vad_parameters")
            if isinstance(vad_params, dict):
                silence_ms = int(max(300.0, self._silence_timeout * 1000.0))
                current_silence = int(vad_params.get("min_silence_duration_ms", silence_ms))
                vad_params["min_silence_duration_ms"] = max(silence_ms, current_silence)
                max_speech = float(vad_params.get("max_speech_duration_s", self._capture_max_duration))
                vad_params["max_speech_duration_s"] = min(self._capture_max_duration, max(1.5, max_speech))
                pad_ms = vad_params.get("speech_pad_ms")
                if pad_ms is None:
                    vad_params["speech_pad_ms"] = 180

        return options, meta

    def _select_primary_segments(self, segments: Sequence[Any]) -> List[Any]:
        """Return only the leading segments that belong to the first utterance."""
        selected: List[Any] = []
        if not segments:
            return selected
        gap_threshold = max(0.5, self._silence_timeout)
        last_end = None
        for segment in segments:
            try:
                seg_start = float(getattr(segment, "start", 0.0) or 0.0)
            except Exception:
                seg_start = 0.0
            try:
                seg_end = float(getattr(segment, "end", seg_start) or seg_start)
            except Exception:
                seg_end = seg_start
            if selected and last_end is not None:
                gap = seg_start - last_end
                if gap > gap_threshold:
                    break
            selected.append(segment)
            last_end = seg_end
        return selected

    def _clean_transcript(self, text: str) -> str:
        if not text:
            return ""
        words = [w for w in re.split(r"\s+", text.strip()) if w]
        if not words:
            return ""
        cleaned: List[str] = []
        repeat_allowance = 2
        for word in words:
            normalized = word.lower()
            if cleaned:
                last = cleaned[-1]
                if normalized == last.lower():
                    repeat_allowance -= 1
                    if repeat_allowance < 0:
                        continue
                else:
                    repeat_allowance = 2
            cleaned.append(word)
        def _strip_repeated_sequences(tokens: List[str]) -> List[str]:
            if len(tokens) < 6:
                return tokens
            output: List[str] = []
            for token in tokens:
                output.append(token)
                for window in range(4, 1, -1):
                    if len(output) >= window * 2:
                        seq1 = [w.lower() for w in output[-window:]]
                        seq2 = [w.lower() for w in output[-window * 2:-window]]
                        if seq1 == seq2:
                            output = output[:-window]
                            break
            return output
        stable = _strip_repeated_sequences(cleaned)
        text_out = " ".join(stable).strip()
        if len(text_out) > 320:
            text_out = text_out[:320]
        return self._post_process_transcript(text_out)

    def _post_process_transcript(self, text: str) -> str:
        if not text:
            return ""
        working = text.strip()
        lowered = working.lower()
        for phrase in self._ignored_phrases:
            if phrase and phrase in lowered:
                return ""
        for alias, replacement in self._command_aliases.items():
            if alias and alias in lowered:
                pattern = re.compile(rf"\b{re.escape(alias)}\b", flags=re.IGNORECASE)
                working = pattern.sub(replacement, working)
                lowered = working.lower()
        working = self._apply_number_replacements(working)
        return re.sub(r"\s+", " ", working).strip()

    def _apply_number_replacements(self, text: str) -> str:
        if not text:
            return ""
        result = text
        stage_map = {
            "stufe eins": "stufe 1",
            "stufe zwei": "stufe 2",
            "stufe drei": "stufe 3",
            "stufe vier": "stufe 4",
            "stufe fuenf": "stufe 5",
            "stufe fünf": "stufe 5",
            "stufe sechs": "stufe 6",
            "stufe sieben": "stufe 7",
            "stufe acht": "stufe 8",
            "stufe neun": "stufe 9",
        }
        for phrase, replacement in stage_map.items():
            pattern = re.compile(rf"\b{phrase}\b", flags=re.IGNORECASE)
            result = pattern.sub(replacement, result)
        for word, digit in NUMBER_WORD_MAP.items():
            pattern = re.compile(rf"\b{re.escape(word)}\b", flags=re.IGNORECASE)
            result = pattern.sub(digit, result)
        return result

    def _apply_tail_filter(self, segments: Sequence[Any]) -> List[Any]:
        """Drop trailing mini segments with filler words or very low confidence."""
        if not segments:
            return []
        if len(segments) == 1:
            candidate = segments[0]
        else:
            candidate = segments[-1]
        text = (getattr(candidate, "text", "") or "").strip()
        if not text:
            return list(segments[:-1]) if len(segments) > 1 else []

        words = [word for word in re.split(r"\s+", text) if word]
        if len(words) >= 3:
            return list(segments)

        first_word = words[0].lower() if words else ""
        try:
            seg_start = float(getattr(candidate, "start", 0.0) or 0.0)
        except Exception:
            seg_start = 0.0
        try:
            seg_end = float(getattr(candidate, "end", seg_start) or seg_start)
        except Exception:
            seg_end = seg_start
        duration = max(0.0, seg_end - seg_start)
        avg_logprob = float(getattr(candidate, "avg_logprob", 0.0) or 0.0)
        low_conf = avg_logprob < -1.0

        should_drop = False
        if first_word in TAIL_FILLER_WORDS and (duration <= 0.7 or low_conf):
            should_drop = True
        elif low_conf and duration <= 0.6 and len(words) <= 2:
            should_drop = True

        if should_drop:
            trimmed = list(segments[:-1])
            if trimmed:
                self.logger.debug("Verwerfe kurzes Nachtragssegment: '%s'", text)
            return trimmed
        return list(segments)

    def _update_profile_history(self, transcript: str, meta: Dict[str, Any]) -> None:
        """Store transcript snippets for future context prompts."""
        if not transcript:
            return
        mode_key, _ = self._resolve_active_profile()
        state = self._profile_state.setdefault(mode_key, {"previous_text": ""})
        history_limit = meta.get("max_history_chars") or self._history_limit
        combined = f"{state.get('previous_text', '')} {transcript}".strip()
        if history_limit and history_limit > 0:
            combined = combined[-history_limit:]
        state["previous_text"] = combined
        state["last_update"] = time.time()

    def _handle_audio_chunk(self, data: bytes) -> None:
        if not data:
            return
        level = self._compute_level_from_bytes(data)
        self._recent_input_level = (self._recent_input_level * 0.7) + (level * 0.3)
        if not self._capture_active:
            self._noise_floor = max(
                0.003,
                (self._noise_floor * self._noise_floor_decay) + (level * (1.0 - self._noise_floor_decay)),
            )
        threshold = max(self._noise_floor * 1.75, 0.018)
        if not self._capture_active and level < threshold and len(self._pending_audio) == 0:
            return
        self._pending_audio.extend(data)
        if len(self._pending_audio) < self._transcription_min_bytes:
            return
        chunk = bytes(self._pending_audio)
        if self._transcription_overlap_bytes > 0 and len(self._pending_audio) > self._transcription_overlap_bytes:
            tail = self._pending_audio[-self._transcription_overlap_bytes :]
            self._pending_audio = bytearray(tail)
        else:
            self._pending_audio = bytearray()
        text = self._transcribe_audio(chunk)
        if text and text != self._last_whisper_output:
            self._last_whisper_output = text
            self.process_speech(text)

    def _transcribe_audio(self, raw_audio: bytes) -> str:
        if not raw_audio:
            return ""
        # Erst versuchen, die Go-Orchestrierung zu nutzen; leiser Fallback bei Fehlern.
        try:
            remote_text = self.speechd_client.recognize(raw_audio, sample_rate=self.config.sample_rate, channels=self.config.channels)
            if isinstance(remote_text, str) and remote_text.strip():
                return self._clean_transcript(remote_text)
        except Exception:
            self.logger.debug("speechtaskd Transkription fehlgeschlagen, nutze lokalen Whisper", exc_info=True)
        if not self._ensure_model_ready():
            return ""
        try:
            audio = np.frombuffer(raw_audio, dtype=np.int16).astype(np.float32)
            if audio.size == 0:
                return ""
            audio = audio / 32768.0
            options, meta = self._build_transcribe_options()
            segments_iter, _ = self._whisper_model.transcribe(audio, **options)
            segment_list = list(segments_iter)
            primary_segments = self._select_primary_segments(segment_list)
            primary_segments = self._apply_tail_filter(primary_segments)
            if not primary_segments and segment_list:
                primary_segments = [segment_list[0]]
            texts: List[str] = []
            for segment in primary_segments:
                seg_text = getattr(segment, "text", "") or ""
                seg_text = seg_text.strip()
                if seg_text:
                    texts.append(seg_text)
            transcript = self._clean_transcript(" ".join(texts).strip())
            if transcript:
                self._update_profile_history(transcript, meta)
            return transcript
        except Exception as exc:
            if self._should_trigger_gpu_fallback(exc):
                self.logger.warning(f"GPU-Transkription fehlgeschlagen ({exc}) - versuche CPU-Fallback.")
                if self._fallback_to_cpu():
                    return self._transcribe_audio(raw_audio)
            self.logger.error(f"Whisper-Transkription fehlgeschlagen: {exc}", exc_info=True)
            return ""

    def get_last_emotion(self):
        """Returns the most recent emotion analysis snapshot."""
        if self._last_emotion_snapshot is None:
            try:
                self._last_emotion_snapshot = self._emotion_analyzer.snapshot().as_dict()
            except Exception:
                self._last_emotion_snapshot = {"label": "neutral", "confidence": 0.0}
        return dict(self._last_emotion_snapshot)

    def get_last_audio_blob(self) -> Optional[bytes]:
        """Returns the most recent captured audio blob for the last command."""
        return self._last_audio_blob



__all__ = ["SpeechRecognizer", "SpeechRecognizerConfig"]
