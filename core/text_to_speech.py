"""
Text-to-Speech Modul fÃ¼r J.A.R.V.I.S.
Verwendet pyttsx3 fÃ¼r deutsche Sprachausgabe
"""

import pyttsx3
import threading
import queue
import time
import os
import platform
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Union

import numpy as np
import soundfile as sf
from scipy import signal

from core.audio_playback import AudioPlaybackWorker, PlaybackRequest
from utils.logger import Logger

class TextToSpeech:
    """Text-zu-Sprache Konverter"""
    
    def __init__(self, settings: Optional[object] = None):
        self.logger = Logger()
        self.engine = None
        self.is_speaking = False
        self.speech_lock = threading.Lock()
        self._queue: "queue.Queue[tuple[str, Optional[str]]]" = queue.Queue(maxsize=200)
        self._worker_stop = threading.Event()
        self._worker_thread: Optional[threading.Thread] = None
        self._backend: str = 'pyttsx3'
        self._xtts = None  # XTTS model instance if used
        self._voice_sample: Optional[str] = None
        self._voice_latents: Optional[Dict[str, Any]] = None
        self._voice_effect: Optional[str] = None
        self._default_xtts_speaker: Optional[str] = None
        self._xtts_speakers: list[str] = []
        self._xtts_cfg: Dict[str, Any] = {}
        self._xtts_multi_speaker: bool = False
        self._missing_speaker_prompted: bool = False
        self._base_rate: int = 180
        self._base_volume: float = 0.8
        self._style_profiles: Dict[str, Dict[str, float]] = {}
        self._current_style: str = 'neutral'
        self._configured_preset: Optional[str] = None
        self._xtts_load_strategy: str = 'on_demand'
        self._xtts_deferred: bool = False
        self._xtts_failed_once: bool = False
        self._xtts_enabled: bool = True
        self._tts_output_dir: Path = Path("output") / "tts_cache"
        self._playback_queue: "queue.Queue[Optional[PlaybackRequest]]" = queue.Queue(maxsize=64)
        self._playback_worker: Optional[AudioPlaybackWorker] = None
        self._tts_cache_root: Path = Path("data") / "tts"
        self._voice_latents_path: Path = self._tts_cache_root / "xtts_voice_latents.pt"
        self._voice_latents_meta: Optional[Dict[str, Any]] = None

        # Einstellungen (duck-typed: erwartet .get)
        self._settings = settings
        self._speech_cfg = {}
        try:
            if self._settings and hasattr(self._settings, 'get'):
                self._speech_cfg = self._settings.get('speech', {}) or {}
        except Exception:
            self._speech_cfg = {}
        try:
            if self._settings and hasattr(self._settings, 'get_model_settings'):
                tts_models = self._settings.get_model_settings('tts') or {}
                xtts_cfg = tts_models.get('xtts') if isinstance(tts_models, dict) else {}
                if isinstance(xtts_cfg, dict):
                    self._xtts_cfg = xtts_cfg
        except Exception:
            self._xtts_cfg = {}

        if self._settings and hasattr(self._settings, 'get_model_load_strategy'):
            try:
                strategy = self._settings.get_model_load_strategy('xtts', default='on_demand', model_type='tts')
                if strategy in ('startup', 'on_demand'):
                    self._xtts_load_strategy = strategy
            except Exception:
                pass
        if self._settings and hasattr(self._settings, 'is_model_enabled'):
            try:
                    self._xtts_enabled = bool(self._settings.is_model_enabled('xtts', default=True, model_type='tts'))
            except Exception:
                self._xtts_enabled = True

        try:
            self._tts_output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            self.logger.warning(f"Could not prepare TTS output directory: {exc}")
        try:
            self._tts_cache_root.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            self.logger.warning(f"Could not prepare TTS cache directory: {exc}")

        self.setup_engine()
        self._init_playback_worker()
        self._start_worker()
    
    def setup_engine(self):
        """TTS-Engine initialisieren"""
        try:
            backend = None
            preset = None
            try:
                backend = self._speech_cfg.get('tts_backend') if isinstance(self._speech_cfg, dict) else None
                preset = self._speech_cfg.get('voice_preset') if isinstance(self._speech_cfg, dict) else None
            except Exception:
                backend, preset = None, None
            self._configured_preset = preset
            self._voice_effect = (preset or '').lower() if preset else None
            desired_backend = None
            try:
                desired_backend = backend.lower().strip() if isinstance(backend, str) else None
            except Exception:
                desired_backend = None
            if desired_backend == 'xtts' and not self._xtts_enabled:
                self.logger.info("XTTS ist deaktiviert; verwende pyttsx3.")
                desired_backend = 'pyttsx3'
            if desired_backend == 'xtts':
                if self._xtts_load_strategy == 'on_demand':
                    self._backend = 'xtts'
                    self._xtts = None
                    self._xtts_deferred = True
                    self.logger.info("XTTS-Backend wird On-Demand initialisiert; Modell wird beim ersten Gebrauch geladen.")
                else:
                    if not self._initialise_xtts_backend():
                        self._backend = 'pyttsx3'
                if self._backend == 'pyttsx3':
                    self._xtts = None
                    self._xtts_deferred = False
            else:
                self._backend = 'pyttsx3'
                self._xtts = None
                self._xtts_deferred = False
            if self._backend == 'pyttsx3':
                self.engine = pyttsx3.init()

            # Deutsche Stimme suchen
            voices = self.engine.getProperty('voices') if self.engine else []
            german_voice = None
            preferred_voice_id = None
            try:
                preferred_voice_id = self._speech_cfg.get('voice_id') if isinstance(self._speech_cfg, dict) else None
            except Exception:
                preferred_voice_id = None

            # 1) explizite voice_id aus Settings bevorzugen
            if preferred_voice_id:
                for voice in voices:
                    if voice.id == preferred_voice_id:
                        german_voice = voice
                        break

            # 2) sonst passende deutsche Stimme suchen
            if not german_voice:
                for voice in voices:
                    try:
                        name_l = voice.name.lower()
                        voice_id_l = str(getattr(voice, 'id', '')).lower()
                        has_lang = False
                        lang_attr = getattr(voice, 'languages', None)
                        if lang_attr:
                            for lang in lang_attr:
                                lang_str = str(lang).lower()
                                if lang_str.startswith('de') or 'deu' in lang_str:
                                    has_lang = True
                                    break
                        if 'german' in name_l or 'de' in voice_id_l or has_lang:
                            german_voice = voice
                            break
                    except Exception:
                        continue

            if self.engine:
                if german_voice:
                    self.engine.setProperty('voice', german_voice.id)
                    self.logger.info(f"Deutsche Stimme gefunden: {german_voice.name}")
                else:
                    # Fallback auf erste verfÃ¼gbare Stimme
                    if voices:
                        self.engine.setProperty('voice', voices[0].id)
                        self.logger.info(f"Fallback-Stimme: {voices[0].name}")

            # Geschwindigkeit und LautstÃ¤rke einstellen
            try:
                rate = int(self._speech_cfg.get('tts_rate', 180)) if isinstance(self._speech_cfg, dict) else 180
            except Exception:
                rate = 180
            try:
                volume = float(self._speech_cfg.get('tts_volume', 0.8)) if isinstance(self._speech_cfg, dict) else 0.8
            except Exception:
                volume = 0.8

            # Einfaches Marvel-JARVIS Preset (Interim)
            try:
                preset_name = (preset or '').lower()
            except Exception:
                preset_name = ''
            if preset_name == 'jarvis_marvel':
                # Tiefer/langsamer und minimal lauter
                rate = max(50, min(300, int(rate * 0.9)))
                volume = max(0.0, min(1.0, float(max(volume, 0.9))))
                # Falls keine konkrete Stimme gesetzt wurde, versuche mÃ¤nnlich klingende DE-Stimme
                if not preferred_voice_id and not german_voice:
                    for voice in voices:
                        try:
                            name_l = voice.name.lower()
                            is_de = ('german' in name_l) or ('de' in voice.id.lower())
                            is_male_hint = any(hint in name_l for hint in ['male', 'mann', 'hans', 'markus'])
                            if is_de and is_male_hint:
                                self.engine.setProperty('voice', voice.id)
                                self.logger.info(f"Preset 'jarvis_marvel': mÃ¤nnliche DE-Stimme gewÃ¤hlt: {voice.name}")
                                break
                        except Exception:
                            continue

            if self.engine:
                bounded_rate = max(50, min(300, rate))
                bounded_volume = max(0.0, min(1.0, volume))
                self.engine.setProperty('rate', bounded_rate)
                self.engine.setProperty('volume', bounded_volume)
                self._base_rate = bounded_rate
                self._base_volume = bounded_volume
            else:
                self._base_rate = max(50, min(300, rate))
                self._base_volume = max(0.0, min(1.0, volume))

            self._initialise_style_profiles()

            self.logger.info("TTS-Engine erfolgreich initialisiert")
        except Exception as e:
            self.logger.error(f"Fehler bei TTS-Initialisierung: {e}")
            self.engine = None

    def _init_playback_worker(self) -> None:
        """Initialisiert den asynchronen Playback-Worker."""
        identifier = self._resolve_output_device_identifier()
        try:
            worker = AudioPlaybackWorker(
                self._playback_queue,
                device_identifier=identifier,
                logger=self.logger,
            )
        except Exception as exc:
            self._playback_worker = None
            self.logger.warning(f"Audio-Playback-Worker deaktiviert: {exc}")
            return
        self._playback_worker = worker
        self._playback_worker.start()

    def _resolve_output_device_identifier(self) -> Optional[Union[int, str]]:
        """Liest die gewuenschte Audio-Ausgabe aus den Einstellungen."""
        audio_cfg: Dict[str, Any] = {}
        try:
            if self._settings and hasattr(self._settings, "get"):
                candidate = self._settings.get("audio", {})  # type: ignore[attr-defined]
                if isinstance(candidate, dict):
                    audio_cfg = candidate
        except Exception:
            audio_cfg = {}

        # Bevorzugt explizite IDs, dann index, dann Name
        raw_id = audio_cfg.get("output_device_id")
        if isinstance(raw_id, int):
            return raw_id
        if isinstance(raw_id, str):
            stripped = raw_id.strip()
            if stripped:
                if stripped.isdigit():
                    return int(stripped)
                return stripped

        raw_index = audio_cfg.get("output_device_index")
        if isinstance(raw_index, int):
            return raw_index
        if isinstance(raw_index, str) and raw_index.strip().isdigit():
            return int(raw_index.strip())

        raw_name = audio_cfg.get("output_device")
        if isinstance(raw_name, str) and raw_name.strip():
            return raw_name.strip()
        return None

    def _next_output_path(self) -> Path:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        return self._tts_output_dir / f"xtts_{timestamp}.wav"

    def _enqueue_playback(self, wav_path: Path) -> None:
        """Leitet die generierte Datei an den Playback-Worker weiter."""
        if not wav_path.exists():
            self.logger.warning("XTTS-Ausgabedatei nicht gefunden: %s", wav_path)
            return
        self._cleanup_old_outputs()
        if self._playback_worker:
            try:
                self._playback_worker.submit(PlaybackRequest(path=wav_path))
                return
            except Exception as exc:
                self.logger.warning(f"Playback-Worker konnte Datei nicht abspielen ({exc}); verwende Fallback.")
        self._fallback_playback(wav_path)

    def _cleanup_old_outputs(self, keep: int = 24) -> None:
        """Entfernt alte TTS-Dateien, um den Cache klein zu halten."""
        try:
            files = sorted(
                [path for path in self._tts_output_dir.glob("xtts_*.wav") if path.is_file()],
                key=lambda item: item.stat().st_mtime,
                reverse=True,
            )
            for stale in files[keep:]:
                try:
                    stale.unlink(missing_ok=True)  # type: ignore[attr-defined]
                except FileNotFoundError:
                    continue
                except Exception:
                    break
        except Exception:
            pass

    def _fallback_playback(self, wav_path: Path) -> None:
        """Fallback-Wiedergabe wenn kein Playback-Worker verfuegbar ist."""
        try:
            import simpleaudio  # type: ignore

            wave_obj = simpleaudio.WaveObject.from_wave_file(str(wav_path))
            play_obj = wave_obj.play()
            play_obj.wait_done()
            return
        except Exception as exc:
            self.logger.debug(f"Simpleaudio-Fallback nicht verfuegbar: {exc}")

        if platform.system().lower().startswith("win"):
            try:
                import winsound  # type: ignore

                try:
                    winsound.PlaySound(None, 0)
                except Exception:
                    pass
                flags = winsound.SND_FILENAME | winsound.SND_NODEFAULT
                winsound.PlaySound(str(wav_path), flags)
                winsound.PlaySound(None, 0)
                return
            except Exception as exc:
                self.logger.warning(f"Winsound-Fallback fehlgeschlagen: {exc}")

        self.logger.warning("Audio konnte nicht abgespielt werden; kein vernuenftiges Backend verfuegbar.")

    def _fallback_basic_tts(self, text: str) -> None:
        """Last-Resort Sprachsynthese ueber pyttsx3 (systemnahe Stimme)."""
        if not text:
            return
        try:
            if self.engine is None:
                self.engine = pyttsx3.init()
                try:
                    self.engine.setProperty('rate', int(self._base_rate))
                    self.engine.setProperty('volume', float(self._base_volume))
                except Exception:
                    pass
        except Exception as init_err:
            self.logger.error(f"pyttsx3-Fallback konnte nicht initialisiert werden: {init_err}")
            return
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as speak_err:
            self.logger.error(f"pyttsx3-Fallback konnte Text nicht sprechen: {speak_err}")

    def _initialise_xtts_backend(self) -> bool:
        """Initialisiert XTTS und gibt True bei Erfolg zurueck."""
        self._xtts_multi_speaker = False
        try:
            import functools
            import importlib
            import inspect
            import torch

            # Torch compatibility patches for XTTS
            try:
                param_mod = importlib.import_module("torch.nn.utils.parametrizations")
                utils_mod = importlib.import_module("torch.nn.utils")
                if not hasattr(param_mod, "weight_norm") and hasattr(utils_mod, "weight_norm"):
                    setattr(param_mod, "weight_norm", getattr(utils_mod, "weight_norm"))
            except Exception:
                pass
            try:
                pytree_mod = importlib.import_module("torch.utils._pytree")
                base_register = getattr(pytree_mod, "_register_pytree_node", None)
                if not hasattr(pytree_mod, "register_pytree_node") or base_register is not None:
                    if base_register is None:
                        base_register = getattr(utils_mod, "register_pytree_node", None)
                    if base_register is None:
                        def compat_register(*_args, **_kwargs):
                            self.logger.warning("XTTS läuft im eingeschränkten PyTree-Kompatibilitätsmodus.")
                        setattr(pytree_mod, "register_pytree_node", compat_register)
                    else:
                        def compat_register(typ, flatten_fn, unflatten_fn, **kwargs):
                            allowed = {"to_dumpable_context", "from_dumpable_context"}
                            filtered = {k: v for k, v in kwargs.items() if k in allowed}
                            return base_register(typ, flatten_fn, unflatten_fn, **filtered)
                        setattr(pytree_mod, "register_pytree_node", compat_register)
            except Exception:
                pass

            from TTS.api import TTS  # type: ignore
            from TTS.tts.configs.xtts_config import XttsConfig  # type: ignore

            add_safe_globals = getattr(torch.serialization, "add_safe_globals", None)
            if callable(add_safe_globals):
                try:
                    add_safe_globals([XttsConfig])
                except Exception:
                    pass
                try:
                    xtts_mod = importlib.import_module('TTS.tts.models.xtts')
                    safe_classes = [obj for obj in xtts_mod.__dict__.values() if inspect.isclass(obj)]
                    add_safe_globals(safe_classes)
                except Exception:
                    pass

            model_name = os.environ.get('JARVIS_XTTS_MODEL', 'tts_models/multilingual/multi-dataset/xtts_v2')
            voice_candidate = None
            try:
                voice_candidate = (self._speech_cfg.get('voice_clone_path')
                                   or self._speech_cfg.get('voice_sample'))
            except Exception:
                voice_candidate = None

            resolved_voice = None
            if voice_candidate:
                candidate_path = os.path.abspath(os.path.expanduser(str(voice_candidate)))
                if os.path.exists(candidate_path):
                    resolved_voice = candidate_path
                else:
                    self.logger.warning(f"XTTS-Voice-Sample nicht gefunden: {candidate_path}")
            if resolved_voice is None:
                default_voice = os.path.abspath(os.path.join('models', 'tts', 'voices', 'Jarvis.wav'))
                if os.path.exists(default_voice):
                    resolved_voice = default_voice
            elif not os.path.isabs(resolved_voice):
                resolved_voice = os.path.abspath(resolved_voice)
            self._voice_sample = resolved_voice
            if self._voice_sample:
                self.logger.info(f"XTTS Voice-Sample: {self._voice_sample}")
            else:
                self.logger.warning("XTTS hat kein Voice-Sample gefunden; bitte Einstellungen pruefen")

            try:
                use_gpu = bool(self._speech_cfg.get('tts_use_gpu')) and torch.cuda.is_available()
            except Exception:
                use_gpu = torch.cuda.is_available()

            try:
                self._xtts = TTS(model_name=model_name, gpu=use_gpu)
            except Exception as xtts_err:
                if "Weights only load failed" in str(xtts_err):
                    torch_load = torch.load
                    torch.load = functools.partial(torch_load, weights_only=False)
                    self._xtts = TTS(model_name=model_name, gpu=use_gpu)
                else:
                    raise
            self._xtts_multi_speaker = self._detect_xtts_multi_speaker()

            self._prepare_xtts_conditioning()
            self._xtts_speakers = self._extract_xtts_speakers()
            self._default_xtts_speaker = self._resolve_default_xtts_speaker()
            if not self._default_xtts_speaker and self._xtts_multi_speaker:
                fallback = self._configured_xtts_speaker() or "speaker_0"
                if fallback and self._is_known_xtts_speaker(fallback):
                    self._default_xtts_speaker = fallback
            if self._default_xtts_speaker:
                self.logger.info(f"XTTS Standardsprecher: {self._default_xtts_speaker}")
                self._persist_xtts_speaker_choice(self._default_xtts_speaker)
            if (
                self._xtts_multi_speaker
                and not self._voice_sample
                and self._voice_latents is None
                and not self._default_xtts_speaker
            ):
                self.logger.warning("XTTS hat kein Voice-Sample und keine Standardstimme; bitte Konfiguration pruefen.")
                self._prompt_for_xtts_speaker()
                self._xtts = None
                return False

            self._backend = 'xtts'
            self._xtts_deferred = False
            self._xtts_failed_once = False
            gpu_status = 'aktiviert' if use_gpu else 'deaktiviert'
            preset = self._configured_preset or 'n/a'
            self.logger.info(f"XTTS-Backend aktiviert (Modell: {model_name}, GPU: {gpu_status}, Preset: {preset})")
            return True
        except Exception as xtts_err:
            self._xtts = None
            self._xtts_deferred = False
            self._xtts_failed_once = True
            self._xtts_multi_speaker = False
            self.logger.warning(f"XTTS konnte nicht initialisiert werden ({xtts_err}); Fallback auf pyttsx3")
            return False

    def _ensure_xtts_backend(self) -> bool:
        """Stellt sicher, dass bei Bedarf ein XTTS-Backend verfuegbar ist."""
        if not self._xtts_enabled:
            self.logger.info("XTTS ist deaktiviert; verwende pyttsx3.")
            self._backend = 'pyttsx3'
            self._xtts = None
            self._xtts_deferred = False
            self._xtts_multi_speaker = False
            if not self.engine:
                try:
                    self.engine = pyttsx3.init()
                except Exception as init_err:
                    self.logger.error(f"pyttsx3-Fallback konnte nicht initialisiert werden: {init_err}")
                    self.engine = None
            return False
        if self._backend != 'xtts':
            return False
        if self._xtts is not None:
            return True
        if self._xtts_load_strategy == 'on_demand':
            self.logger.info("XTTS-Backend wird On-Demand geladen...")
        success = self._initialise_xtts_backend()
        if success:
            return True
        self._backend = 'pyttsx3'
        self._xtts = None
        self._xtts_deferred = False
        self._xtts_multi_speaker = False
        if not self.engine:
            try:
                self.engine = pyttsx3.init()
            except Exception as init_err:
                self.logger.error(f"pyttsx3-Fallback konnte nicht initialisiert werden: {init_err}")
                self.engine = None
        return False

    def list_available_models(self) -> Dict[str, Dict[str, Any]]:
        """Gibt eine Modell-Uebersicht fuer die TTS-Konfiguration zurueck."""
        catalog: Dict[str, Dict[str, Any]] = {}
        backend_name = ''
        try:
            backend_name = str(self._speech_cfg.get('tts_backend', '')).strip().lower()
        except Exception:
            backend_name = ''
        xtts_supported = False
        try:
            import importlib.util
            xtts_supported = importlib.util.find_spec('TTS') is not None
        except Exception:
            xtts_supported = False
        if xtts_supported or backend_name == 'xtts':
            catalog['xtts'] = {
                'display_name': 'XTTS v2',
                'description': 'Neuronales Mehrsprach-TTS mit Sprecher-Stimmprofilen',
                'available': xtts_supported,
                'loaded': bool(self._xtts),
                'active': self._backend == 'xtts' and self._xtts_enabled,
                'enabled': self._xtts_enabled,
                'default_strategy': 'on_demand',
            }
        return catalog
    
    def _start_worker(self) -> None:
        """Startet den Hintergrund-Worker, der die Sprachwarteschlange abarbeitet."""
        if self._worker_thread and self._worker_thread.is_alive():
            return
        self._worker_stop.clear()
        self._worker_thread = threading.Thread(target=self._worker, name="TTSWorker", daemon=True)
        self._worker_thread.start()
    
    def _initialise_style_profiles(self) -> None:
        self._style_profiles = {
            'neutral': {
                'rate': float(self._base_rate),
                'volume': float(self._base_volume),
            },
            'freundlich': {
                'rate': float(self._base_rate) * 1.05,
                'volume': min(1.0, float(self._base_volume) + 0.1),
            },
            'professionell': {
                'rate': float(self._base_rate) * 0.92,
                'volume': float(self._base_volume),
            },
            'humorvoll': {
                'rate': float(self._base_rate) * 1.1,
                'volume': min(1.0, float(self._base_volume) + 0.05),
            },
        }

    def set_style(self, style: str) -> None:
        """Setzt den aktiven Sprachstil (neutral, freundlich, professionell, humorvoll)."""
        normalized = (style or 'neutral').strip().lower()
        if normalized not in self._style_profiles:
            normalized = 'neutral'
        self._current_style = normalized
        try:
            self._apply_style(normalized)
        except Exception as exc:
            self.logger.debug(f"Stil konnte nicht angewendet werden: {exc}")

    def _apply_style(self, style: Optional[str]) -> None:
        target_style = (style or self._current_style or 'neutral').strip().lower()
        if target_style not in self._style_profiles:
            target_style = 'neutral'
        profile = self._style_profiles[target_style]
        if self._backend == 'xtts':
            if target_style in {'humorvoll', 'freundlich'}:
                self._voice_effect = 'jarvis_marvel'
            elif target_style == 'professionell':
                self._voice_effect = None
            else:
                self._voice_effect = None
            return
        if not self.engine:
            return
        try:
            self.engine.setProperty('rate', max(50, min(300, int(profile['rate']))))
            self.engine.setProperty('volume', max(0.0, min(1.0, float(profile['volume']))))
        except Exception as exc:
            self.logger.debug(f"Setzen des Stils fehlgeschlagen: {exc}")

    def speak(self, text: str, *, style: Optional[str] = None):
        """Legt Text in die Warteschlange; wird sequenziell gesprochen."""
        if not text:
            return

        if self._backend == 'xtts':
            if not self._ensure_xtts_backend():
                self.logger.warning("XTTS-Backend nicht initialisiert; Text verworfen")
                return
        if self._backend != 'xtts' and not self.engine:
            self.logger.warning("TTS-Engine nicht initialisiert; Text verworfen")
            return
        try:
            # Kurze Normalisierung: Whitespace
            prepared = text.strip()
            if not prepared:
                return
            self._queue.put_nowait((prepared, style))
            prefix = 'XTTS' if self._backend == 'xtts' and self._xtts is not None else 'TTS'
            suffix = '...' if len(prepared) > 80 else ''
            self.logger.info(f"{prefix} queued: {prepared[:80]}{suffix}")
        except queue.Full:
            self.logger.error("TTS-Queue voll; verwerfe aelteste Eintraege und fuege neu hinzu")
            try:
                _ = self._queue.get_nowait()
            except Exception:
                pass
            try:
                self._queue.put_nowait((prepared, style))
            except Exception:
                pass
    
    def _worker(self) -> None:
        """Abarbeitung der TTS-Warteschlange in einem einzigen Thread (Thread-sicher fuer pyttsx3)."""
        while not self._worker_stop.is_set():
            try:
                try:
                    item = self._queue.get(timeout=0.25)
                except queue.Empty:
                    continue
                if not item:
                    continue
                text, style = item
                if not text:
                    continue
                effective_style = style or self._current_style
                if effective_style:
                    self._apply_style(effective_style)
                    self._current_style = effective_style
                with self.speech_lock:
                    self.is_speaking = True
                    try:
                        if self._backend == 'xtts':
                            if self._xtts is None and not self._ensure_xtts_backend():
                                self.logger.warning("XTTS-Backend nicht verfuegbar; Text verworfen")
                            elif self._backend == 'xtts' and self._xtts is not None:
                                self._speak_xtts(text)
                            elif self.engine is not None:
                                self.engine.say(text)
                                self.engine.runAndWait()
                            else:
                                self.logger.warning("Kein TTS-Backend initialisiert; Text verworfen")
                        elif self.engine is not None:
                            self.engine.say(text)
                            self.engine.runAndWait()
                        else:
                            self.logger.warning("Kein TTS-Backend initialisiert; Text verworfen")
                    except Exception as e:
                        self.logger.error(f"Fehler bei Sprachausgabe: {e}")
                    finally:
                        self.is_speaking = False
                        self._queue.task_done()
            except Exception as loop_err:
                # Schutz gegen unerwartete Worker-Fehler
                self.logger.error(f"Fehler im TTS-Worker: {loop_err}")
                time.sleep(0.5)
    
    def stop_speaking(self):
        """Stoppt aktuelle Sprachausgabe"""
        try:
            if self.engine:
                # Stoppt aktuelle Ausgabe
                if self.is_speaking:
                    self.engine.stop()
                    self.is_speaking = False
                # Warteschlange leeren
                while not self._queue.empty():
                    try:
                        self._queue.get_nowait()
                        self._queue.task_done()
                    except Exception:
                        break
                self.logger.info("Sprachausgabe gestoppt und Queue geleert")
            if self._playback_worker:
                self._playback_worker.stop_active()
        except Exception as e:
            self.logger.error(f"Fehler beim Stoppen der Sprachausgabe: {e}")
    
    def is_busy(self):
        """PrÃ¼ft ob TTS gerade aktiv ist"""
        return self.is_speaking or not self._queue.empty()

    def shutdown(self) -> None:
        """Stoppt Worker-Thread und bereinigt Engine."""
        try:
            self._worker_stop.set()
            if self._worker_thread and self._worker_thread.is_alive():
                self._worker_thread.join(timeout=1.0)
        except Exception:
            pass
        try:
            if self._playback_worker:
                self._playback_worker.stop(drain=False)
        except Exception:
            pass
        try:
            if self.engine:
                self.engine.stop()
        except Exception:
            pass
    
    def set_rate(self, rate):
        """Setzt Sprechgeschwindigkeit (50-300)"""
        try:
            if self.engine:
                self.engine.setProperty('rate', max(50, min(300, rate)))
                self.logger.info(f"Sprechgeschwindigkeit auf {rate} gesetzt")
                # In Settings persistieren, falls verfÃ¼gbar
                try:
                    if self._settings and hasattr(self._settings, 'update_speech_settings'):
                        self._settings.update_speech_settings(tts_rate=int(max(50, min(300, rate))))
                except Exception:
                    pass
        except Exception as e:
            self.logger.error(f"Fehler beim Setzen der Sprechgeschwindigkeit: {e}")
    
    def set_volume(self, volume):
        """Setzt LautstÃ¤rke (0.0-1.0)"""
        try:
            if self.engine:
                self.engine.setProperty('volume', max(0.0, min(1.0, volume)))
                self.logger.info(f"LautstÃ¤rke auf {volume} gesetzt")
                # In Settings persistieren, falls verfÃ¼gbar
                try:
                    if self._settings and hasattr(self._settings, 'update_speech_settings'):
                        self._settings.update_speech_settings(tts_volume=float(max(0.0, min(1.0, volume))))
                except Exception:
                    pass
        except Exception as e:
            self.logger.error(f"Fehler beim Setzen der LautstÃ¤rke: {e}")
    
    def get_voices(self):
        """Gibt verfÃ¼gbare Stimmen zurÃ¼ck"""
        try:
            if self.engine:
                voices = self.engine.getProperty('voices')
                return [(voice.id, voice.name) for voice in voices]
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen der Stimmen: {e}")
        return []
    
    def set_voice(self, voice_id):
        """Setzt spezifische Stimme"""
        try:
            if self._backend == 'pyttsx3' and self.engine:
                self.engine.setProperty('voice', voice_id)
                self.logger.info(f"Stimme geÃ¤ndert: {voice_id}")
                # In Settings persistieren, falls verfÃ¼gbar
                try:
                    if self._settings and hasattr(self._settings, 'update_speech_settings'):
                        self._settings.update_speech_settings(voice_id=voice_id)
                except Exception:
                    pass
            else:
                self.logger.info("set_voice() wird vom aktuellen Backend nicht unterstÃ¼tzt oder ignoriert (XTTS)")
        except Exception as e:
            self.logger.error(f"Fehler beim Setzen der Stimme: {e}")

    def _prepare_xtts_conditioning(self) -> None:
        """Bereitet XTTS-Stimmlatenzen einmalig vor, um wiederholtes Cloning zu vermeiden."""
        if not self._xtts:
            return
        if self._voice_latents:
            return
        if self._voice_sample and self._load_xtts_conditioning_cache():
            return
        if not self._voice_sample or not os.path.exists(self._voice_sample):
            self._voice_latents = None
            self._clear_xtts_conditioning_cache()
            return
        try:
            conditioning = self._xtts.synthesizer.tts_model.get_conditioning_latents(
                audio_path=self._voice_sample
            )
            if isinstance(conditioning, (list, tuple)) and len(conditioning) == 2:
                gpt_latent, speaker_embedding = conditioning
                self._voice_latents = {
                    "gpt_cond_latent": gpt_latent,
                    "speaker_embedding": speaker_embedding,
                }
                self._persist_xtts_conditioning_cache()
                self.logger.info("XTTS Voice-Sample vorverarbeitet (Latents gecached)")
            else:
                self._voice_latents = None
                self._clear_xtts_conditioning_cache()
                self.logger.warning("XTTS lieferte unerwartete Conditioning-Daten; verwende speaker_wav direkt")
        except Exception as err:
            self._voice_latents = None
            self._clear_xtts_conditioning_cache()
            self.logger.warning(f"XTTS-Latents konnten nicht vorbereitet werden: {err}")

    def _load_xtts_conditioning_cache(self) -> bool:
        """Lädt vorberechnete XTTS-Latents von der Festplatte, falls verfügbar."""
        if not self._voice_sample or not self._voice_latents_path.exists():
            return False
        try:
            import torch

            payload = torch.load(str(self._voice_latents_path), map_location="cpu")
            if not isinstance(payload, dict):
                return False
            gpt_latent = payload.get("gpt_cond_latent")
            speaker_embedding = payload.get("speaker_embedding")
            cached_sample = payload.get("sample_path")
            cached_mtime = payload.get("sample_mtime")
            if gpt_latent is None or speaker_embedding is None:
                return False
            sample_abs = os.path.abspath(self._voice_sample)
            if cached_sample and os.path.exists(sample_abs):
                if os.path.abspath(str(cached_sample)) != sample_abs:
                    return False
                if cached_mtime is not None:
                    try:
                        current_mtime = os.path.getmtime(sample_abs)
                        if abs(current_mtime - float(cached_mtime)) > 1e-3:
                            return False
                    except Exception:
                        return False
            self._voice_latents = {
                "gpt_cond_latent": gpt_latent,
                "speaker_embedding": speaker_embedding,
            }
            self._voice_latents_meta = {
                "path": cached_sample,
                "mtime": cached_mtime,
            }
            self.logger.info("XTTS Voice-Latents aus Cache geladen.")
            return True
        except Exception as err:
            self.logger.debug(f"XTTS conditioning cache konnte nicht geladen werden: {err}")
            return False

    def _persist_xtts_conditioning_cache(self) -> None:
        """Persistiert die berechneten Latents für zukünftige Starts."""
        if not self._voice_latents or not self._voice_sample:
            self._clear_xtts_conditioning_cache()
            return
        try:
            import torch

            def _normalize(value: Any) -> Any:
                try:
                    if isinstance(value, torch.Tensor):
                        return value.detach().cpu()
                except Exception:
                    pass
                return value

            sample_abs = os.path.abspath(self._voice_sample)
            sample_mtime = None
            try:
                if os.path.exists(sample_abs):
                    sample_mtime = os.path.getmtime(sample_abs)
            except Exception:
                sample_mtime = None
            payload = {
                "gpt_cond_latent": _normalize(self._voice_latents.get("gpt_cond_latent")),
                "speaker_embedding": _normalize(self._voice_latents.get("speaker_embedding")),
                "sample_path": sample_abs,
                "sample_mtime": sample_mtime,
                "created": time.time(),
            }
            self._voice_latents_path.parent.mkdir(parents=True, exist_ok=True)
            torch.save(payload, str(self._voice_latents_path))
            self._voice_latents_meta = {"path": sample_abs, "mtime": sample_mtime}
            self.logger.info("XTTS Voice-Latents gespeichert.")
        except Exception as err:
            self.logger.debug(f"XTTS conditioning cache konnte nicht gespeichert werden: {err}")

    def _clear_xtts_conditioning_cache(self) -> None:
        """Entfernt den gespeicherten Latents-Cache."""
        self._voice_latents_meta = None
        try:
            if self._voice_latents_path.exists():
                self._voice_latents_path.unlink()
        except Exception as err:
            self.logger.debug(f"XTTS conditioning cache konnte nicht gelöscht werden: {err}")

    def _apply_voice_effects(self, wav_path: str) -> None:
        """Optional post-processing for generated audio (e.g., Jarvis Marvel effect)."""
        if not self._voice_effect:
            return
        effect = self._voice_effect
        if effect != 'jarvis_marvel':
            return
        try:
            data, sample_rate = sf.read(wav_path)
            if data.size == 0:
                return
            if data.ndim == 1:
                data = data[:, None]
            # High-pass filter to remove rumble and emphasize clarity
            hp_cutoff = 120.0
            if sample_rate > hp_cutoff * 2:
                b_hp, a_hp = signal.butter(2, hp_cutoff / (sample_rate / 2.0), btype='highpass')
                high = signal.lfilter(b_hp, a_hp, data, axis=0)
            else:
                high = data
            processed = data * 0.82 + high * 0.45
            # Subtle metallic resonance via short multi-tap delay
            delay_ms = 45
            decay = 0.32
            delay_samples = int(sample_rate * delay_ms / 1000.0)
            if delay_samples > 0:
                tail = np.zeros((processed.shape[0] + delay_samples, processed.shape[1]), dtype=processed.dtype)
                tail[: processed.shape[0]] += processed
                tail[delay_samples:] += processed * decay
                processed = tail
            max_val = np.max(np.abs(processed))
            if max_val > 0:
                processed = processed / max(max_val, 1.0) * 0.95
            sf.write(wav_path, processed.astype(np.float32), sample_rate)
        except Exception as err:
            self.logger.warning(f'Jarvis-Stimmeneffekt konnte nicht angewendet werden: {err}')

    def _xtts_generate_waveform(self, tts_kwargs: Dict[str, Any]) -> tuple[np.ndarray, int]:
        """Erzeugt eine Wellenform direkt via XTTS, um Dateihandles zu vermeiden."""
        if not self._xtts:
            raise RuntimeError("XTTS Backend nicht initialisiert")
        infer_kwargs = dict(tts_kwargs)
        infer_kwargs.pop("file_path", None)
        waveform = self._xtts.tts(**infer_kwargs)
        sample_rate: Optional[int] = None
        if isinstance(waveform, tuple):
            if len(waveform) >= 2 and isinstance(waveform[1], (int, float)):
                sample_rate = int(float(waveform[1]))
                waveform = waveform[0]
            else:
                waveform = waveform[0]
        if sample_rate is None:
            sample_rate = getattr(self._xtts, "output_sample_rate", None)
            if not sample_rate:
                sample_rate = getattr(self._xtts, "sample_rate", None)
        if not sample_rate:
            sample_rate = 24000
        array = np.asarray(waveform, dtype=np.float32)
        if array.ndim > 1 and array.shape[0] == 1:
            array = array[0]
        return array, int(sample_rate)

    def _write_waveform_to_file(self, wav_path: Path, waveform: np.ndarray, sample_rate: int) -> None:
        """Persistiert eine Wellenform als WAV-Datei."""
        if sample_rate <= 0:
            sample_rate = 24000
        sf.write(str(wav_path), waveform, sample_rate)

    # ------------------------------------------------------------------
    # XTTS Backend Helpers
    # ------------------------------------------------------------------
    def _speak_xtts(self, text: str) -> None:
        """Erzeugt Audio via XTTS und leitet es an den Playback-Worker weiter."""
        if not self._xtts:
            return
        wav_path = self._next_output_path()
        try:
            if self._voice_latents is None and self._voice_sample and os.path.exists(self._voice_sample):
                self._prepare_xtts_conditioning()

            tts_kwargs = dict(text=text, file_path=str(wav_path), language="de")
            used_conditioning = False
            if self._voice_latents:
                try:
                    tts_kwargs.update(self._voice_latents)
                    used_conditioning = True
                except Exception as cond_err:
                    self.logger.debug(f"XTTS-Latents konnten nicht uebernommen werden: {cond_err}")
                    used_conditioning = False
            if used_conditioning:
                tts_kwargs.pop("speaker_wav", None)
            else:
                sample_path = None
                if self._voice_sample and os.path.exists(self._voice_sample):
                    try:
                        sample_path = os.path.abspath(self._voice_sample)
                    except Exception:
                        sample_path = self._voice_sample
                if sample_path:
                    tts_kwargs["speaker_wav"] = sample_path

                speaker_id = None
                if "speaker_wav" not in tts_kwargs:
                    speaker_id = self._configured_xtts_speaker() or self._default_xtts_speaker
                    available_speakers = self._xtts_speakers
                    if isinstance(available_speakers, dict):
                        available_speakers = list(available_speakers.keys())
                    if not speaker_id and available_speakers:
                        try:
                            speaker_id = next((str(name) for name in available_speakers if isinstance(name, (str, bytes))), None)
                        except Exception:
                            speaker_id = None
                    if speaker_id and self._is_known_xtts_speaker(speaker_id):
                        tts_kwargs.setdefault("speaker", speaker_id)

            if (
                self._xtts_multi_speaker
                and "speaker" not in tts_kwargs
            ):
                fallback_speaker = (
                    self._default_xtts_speaker
                    or self._configured_xtts_speaker()
                    or self._resolve_default_xtts_speaker()
                )
                if fallback_speaker and self._is_known_xtts_speaker(fallback_speaker):
                    tts_kwargs["speaker"] = fallback_speaker
                    if not self._default_xtts_speaker:
                        self._default_xtts_speaker = fallback_speaker
                        self._persist_xtts_speaker_choice(fallback_speaker)
                else:
                    self._prompt_for_xtts_speaker()
                    self.logger.error("XTTS benoetigt eine definierte Sprecher-ID bei Multi-Speaker-Modellen.")
                    self._fallback_basic_tts(text)
                    return

            if not (used_conditioning or "speaker_wav" in tts_kwargs or "speaker" in tts_kwargs):
                self.logger.error("XTTS benoetigt ein Voice-Sample, eine Speaker-ID oder vorbereitete Latents; bitte Einstellungen pruefen")
                self._prompt_for_xtts_speaker()
                self._fallback_basic_tts(text)
                return

            synthesis_successful = False
            try:
                self._xtts.tts_to_file(**tts_kwargs)
                synthesis_successful = True
            except KeyError as key_err:
                missing = tts_kwargs.pop("speaker", None)
                self.logger.warning(f"XTTS-Generierung schlug fehl (KeyError: {key_err}); entferne Sprecher '{missing}' und versuche Voice-Sample.")
                try:
                    if "speaker_wav" not in tts_kwargs and self._voice_sample:
                        tts_kwargs["speaker_wav"] = self._voice_sample
                    self._xtts.tts_to_file(**tts_kwargs)
                    synthesis_successful = True
                except Exception as retry_err:
                    self.logger.error(f"XTTS-Retry ohne Sprecher fehlgeschlagen: {retry_err}")
            except OSError as os_err:
                if getattr(os_err, "winerror", None) == 6:
                    self.logger.warning("XTTS tts_to_file meldet WinError 6; versuche alternative Synthese.")
                    try:
                        waveform, sample_rate = self._xtts_generate_waveform(tts_kwargs)
                        self._write_waveform_to_file(wav_path, waveform, sample_rate)
                        synthesis_successful = True
                    except Exception as fallback_err:
                        self.logger.error(f"XTTS-Fallback fehlgeschlagen: {fallback_err}")
                        synthesis_successful = False
                else:
                    self.logger.error(f"XTTS-Generierung fehlgeschlagen: {os_err}")
            except Exception as gen_err:
                self.logger.error(f"XTTS-Generierung fehlgeschlagen: {gen_err}")

            if not synthesis_successful:
                try:
                    if wav_path.exists():
                        wav_path.unlink()
                except Exception:
                    pass
                self.logger.warning("XTTS konnte keinen Audio-Output generieren; verwende pyttsx3-Fallback.")
                self._fallback_basic_tts(text)
                return

            try:
                self._apply_voice_effects(str(wav_path))
            except Exception as effect_err:
                self.logger.debug(f"XTTS-Nachbearbeitung konnte nicht angewendet werden: {effect_err}")
        except Exception as gen_err:
            self.logger.error(f"XTTS-Generierung fehlgeschlagen: {gen_err}")
            try:
                if wav_path.exists():
                    wav_path.unlink()
            except Exception:
                pass
            self._fallback_basic_tts(text)
            return
        self._enqueue_playback(wav_path)

    def _configured_xtts_speaker(self) -> Optional[str]:
        """Liest den bevorzugten XTTS-Sprecher aus Settings oder Model-Konfiguration."""
        try:
            if isinstance(self._speech_cfg, dict):
                configured = self._speech_cfg.get('tts_xtts_speaker')
                if isinstance(configured, str) and configured.strip():
                    return configured.strip()
        except Exception:
            pass
        candidate = self._xtts_cfg.get('default_speaker')
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
        env_default = os.environ.get('JARVIS_XTTS_DEFAULT_SPEAKER')
        if env_default and env_default.strip():
            return env_default.strip()
        return None

    def _detect_xtts_multi_speaker(self) -> bool:
        """Prueft, ob das geladene Modell mehrere Sprecher unterstuetzt."""
        if not self._xtts:
            return False
        if bool(getattr(self._xtts, 'is_multi_speaker', False)):
            return True
        synthesizer = getattr(self._xtts, 'synthesizer', None)
        model = getattr(synthesizer, 'tts_model', None)
        if model is None:
            return False
        if hasattr(model, 'is_multi_speaker'):
            try:
                return bool(getattr(model, 'is_multi_speaker'))
            except Exception:
                return False
        num_speakers = getattr(model, 'num_speakers', 0)
        try:
            return int(num_speakers or 0) > 1
        except Exception:
            return False

    def _prompt_for_xtts_speaker(self) -> None:
        """Schreibt einen Hinweis ins Security-Log, falls ein Speaker fehlt."""
        if self._missing_speaker_prompted:
            return
        self._missing_speaker_prompted = True
        message = ("XTTS benoetigt eine definierte Standardstimme. "
                   "Setze 'speech.tts_xtts_speaker' oder 'models.tts.xtts.default_speaker'.")
        self.logger.warning(message)
        try:
            security_log = Path("logs") / "security.log"
            security_log.parent.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.utcnow().isoformat()
            with security_log.open('a', encoding='utf-8') as handle:
                handle.write(f"{timestamp} - XTTS - {message}\n")
        except Exception:
            pass

    def _extract_xtts_speakers(self) -> list[str]:
        """Liest verfuegbare XTTS-Sprecher aus dem Modell aus."""
        speakers: list[str] = []
        try:
            if not self._xtts:
                return speakers
            raw = getattr(self._xtts, 'speakers', None)
            if isinstance(raw, dict):
                speakers = [str(name) for name in raw.keys()]
            elif isinstance(raw, (list, tuple, set)):
                speakers = [str(name) for name in raw]
        except Exception as err:
            self.logger.debug(f"XTTS-Sprecher konnten nicht ermittelt werden: {err}")
        return speakers

    def _is_known_xtts_speaker(self, speaker: Optional[str]) -> bool:
        """Prueft, ob ein Sprecher im XTTS-Modell vorhanden ist (oder keine Liste verfuegbar ist)."""
        if not speaker:
            return False
        candidates = self._xtts_speakers
        if isinstance(candidates, dict):
            candidates = list(candidates.keys())
        if not candidates:
            # Keine explizite Liste -> nicht blockieren
            return True
        try:
            return speaker in [str(name) for name in candidates]
        except Exception:
            return False

    def _resolve_default_xtts_speaker(self) -> Optional[str]:
        """Waehlt eine sinnvolle deutsche XTTS-Stimme als Fallback."""
        try:
            configured = self._configured_xtts_speaker()
            if configured:
                if not self._xtts_speakers or configured in self._xtts_speakers:
                    return configured
            if not self._xtts_speakers:
                return None
            for speaker in self._xtts_speakers:
                lowered = speaker.lower()
                if 'de' in lowered or 'german' in lowered:
                    return speaker
            return self._xtts_speakers[0]
        except Exception as err:
            self.logger.debug(f"XTTS-Standardsprecher konnte nicht bestimmt werden: {err}")
            return None

    def _persist_xtts_speaker_choice(self, speaker: str) -> None:
        """Speichert die automatisch gewaehlt XTTS-Stimme in den Einstellungen."""
        if not speaker or not isinstance(self._speech_cfg, dict):
            return
        if self._speech_cfg.get('tts_xtts_speaker'):
            return
        self._speech_cfg['tts_xtts_speaker'] = speaker
        try:
            if self._settings and hasattr(self._settings, 'update_speech_settings'):
                self._settings.update_speech_settings(tts_xtts_speaker=speaker)
        except Exception:
            pass
