"""
Queued audio playback worker for Jarvis.
Ensures each clip opens the audio device fresh to avoid stale handles.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from pathlib import Path
from queue import Empty, Queue
from typing import Optional, Union

try:
    import sounddevice as sd  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    sd = None  # type: ignore
try:
    import soundfile as sf  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    sf = None  # type: ignore
try:
    import simpleaudio as sa  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    sa = None  # type: ignore
else:
    sa: Optional[object]
# We keep a string description purely for logging purposes.
if sd is not None and sf is not None:
    DEFAULT_BACKEND = "sounddevice"
elif sa is not None:
    DEFAULT_BACKEND = "simpleaudio"
else:
    DEFAULT_BACKEND = None

from utils.logger import Logger


@dataclass
class PlaybackRequest:
    """Small container for playback items."""

    path: Path


class AudioPlaybackWorker:
    """
    Consumes playback requests from a queue and streams them via sounddevice.

    The worker re-initialises the device for every clip and retries once if a WinError 6
    occurs, which is commonly triggered when the underlying handle becomes invalid.
    """

    def __init__(
        self,
        queue: "Queue[Optional[PlaybackRequest]]",
        *,
        device_identifier: Optional[Union[int, str]] = None,
        logger: Optional[Logger] = None,
    ) -> None:
        self.queue = queue
        self.device_identifier = device_identifier
        self.logger = logger or Logger()
        self._running = threading.Event()
        self._running.set()
        self._thread: Optional[threading.Thread] = None
        self._device_index: Optional[int] = None
        self._device_name: Optional[str] = None
        self._current_simple_play: Optional[object] = None

        if DEFAULT_BACKEND is None:
            raise RuntimeError(
                "Kein Audiowiedergabe-Backend verfuegbar (weder sounddevice+soundfile noch simpleaudio installiert)."
            )

        self._backend = DEFAULT_BACKEND

        if self._backend == "sounddevice":
            self._resolve_device()
            self.logger.info(
                "Audio-Playback-Worker gestartet (Backend: sounddevice, Device: %s)",
                self._device_name if self._device_name else "Default",
            )
        else:
            self.logger.info("Audio-Playback-Worker gestartet (Backend: simpleaudio)")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run, name="JarvisAudioPlayback", daemon=True)
        self._thread.start()

    def stop(self, *, drain: bool = False) -> None:
        self._running.clear()
        self.stop_active()
        if not drain:
            self._clear_queue()
        try:
            self.queue.put_nowait(None)
        except Exception:
            pass
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.5)

    def submit(self, request: PlaybackRequest) -> None:
        if not isinstance(request, PlaybackRequest):
            raise TypeError("Playback request must be a PlaybackRequest instance")
        if not request.path.exists():
            self.logger.warning("Playback file does not exist: %s", request.path)
            return
        try:
            self.queue.put_nowait(request)
        except Exception as exc:
            self.logger.error("Playback queue overflow: %s", exc)

    def stop_active(self) -> None:
        """Stop the currently playing clip without terminating the worker."""
        if self._backend == "sounddevice" and sd is not None:
            try:
                sd.stop()
            except Exception:
                pass
        elif self._backend == "simpleaudio":
            try:
                if self._current_simple_play and hasattr(self._current_simple_play, "stop"):
                    self._current_simple_play.stop()  # type: ignore[attr-defined]
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _run(self) -> None:
        while self._running.is_set():
            try:
                item = self.queue.get(timeout=0.2)
            except Empty:
                continue
            if item is None:
                self.queue.task_done()
                break
            try:
                self._play_with_retry(item.path)
            finally:
                self.queue.task_done()

    def _play_with_retry(self, path: Path) -> None:
        attempts = 0
        while attempts < 2:
            try:
                self._play_file(path)
                return
            except OSError as exc:
                attempts += 1
                self.logger.warning("Playback OSError (attempt %s): %s", attempts, exc)
                time.sleep(0.2)
                self._resolve_device(force=True)
            except Exception as exc:  # pragma: no cover - unexpected
                self.logger.error("Playback failed: %s", exc, exc_info=True)
                return
        self.logger.error("Playback failed after retry: %s", path)

    def _play_file(self, path: Path) -> None:
        if self._backend == "sounddevice":
            if sd is None or sf is None:
                raise RuntimeError("sounddevice backend not available")
            data, sample_rate = sf.read(str(path), dtype="float32")
            if data.size == 0:
                self.logger.warning("Skipping empty audio buffer: %s", path)
                return
            try:
                sd.play(data, sample_rate, device=self._device_index, blocking=True)
            finally:
                try:
                    sd.stop()
                except Exception:
                    pass
        else:
            if sa is None:
                raise RuntimeError("simpleaudio backend not available")
            wave_obj = sa.WaveObject.from_wave_file(str(path))  # type: ignore[attr-defined]
            play_obj = wave_obj.play()  # type: ignore[attr-defined]
            self._current_simple_play = play_obj
            play_obj.wait_done()
            self._current_simple_play = None

    def _resolve_device(self, force: bool = False) -> None:
        if self._backend != "sounddevice" or sd is None:
            return
        if not force and (self._device_index is not None or self.device_identifier is None):
            return
        identifier = self.device_identifier
        try:
            devices = sd.query_devices()
        except Exception as exc:
            self.logger.warning("Could not query audio devices: %s", exc)
            self._device_index = None
            self._device_name = None
            return

        chosen_index: Optional[int] = None
        chosen_name: Optional[str] = None
        if isinstance(identifier, int):
            if 0 <= identifier < len(devices):
                info = devices[identifier]
                if info.get("max_output_channels", 0) > 0:
                    chosen_index = identifier
                    chosen_name = str(info.get("name", identifier))
        elif isinstance(identifier, str):
            normalized = identifier.strip().lower()
            for idx, info in enumerate(devices):
                if info.get("max_output_channels", 0) <= 0:
                    continue
                name = str(info.get("name", "")).lower()
                if normalized in name:
                    chosen_index = idx
                    chosen_name = str(info.get("name", idx))
                    break
        if chosen_index is None and devices:
            # fallback to default output device
            default_index = sd.default.device[1] if isinstance(sd.default.device, (list, tuple)) else None
            if isinstance(default_index, int) and 0 <= default_index < len(devices):
                info = devices[default_index]
                if info.get("max_output_channels", 0) > 0:
                    chosen_index = default_index
                    chosen_name = str(info.get("name", default_index))

        self._device_index = chosen_index
        self._device_name = chosen_name
        if self._device_index is not None and self._device_name:
            self.logger.info("Audio playback uses device %s (index %s)", self._device_name, self._device_index)
        elif self._device_index is None:
            self.logger.info("Audio playback uses default output device")

    def _clear_queue(self) -> None:
        try:
            while True:
                self.queue.get_nowait()
                self.queue.task_done()
        except Empty:
            pass
