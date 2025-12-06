"""
XTTS (Coqui TTS) Text-to-Speech Engine for J.A.R.V.I.S.

Provides high-quality neural text-to-speech using XTTS-v2 model.
Falls back to pyttsx3 if XTTS is not available.
"""
from __future__ import annotations

import logging
import os
import tempfile
import wave
from pathlib import Path
from typing import Optional, Union

try:
    from TTS.api import TTS
    XTTS_AVAILABLE = True
except ImportError:
    XTTS_AVAILABLE = False
    TTS = None

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    pyttsx3 = None

import torch

logger = logging.getLogger(__name__)


class XTTSTTS:
    """
    Text-to-Speech engine using XTTS-v2 (Coqui TTS).
    
    Falls back to pyttsx3 if XTTS is not available or GPU is not present.
    """

    def __init__(
        self,
        *,
        model_name: str = "tts_models/multilingual/multi-dataset/xtts_v2",
        language: str = "de",
        speaker_wav: Optional[Union[str, Path]] = None,
        use_gpu: bool = True,
        fallback_to_pyttsx3: bool = True,
    ):
        """
        Initialize XTTS TTS engine.
        
        Args:
            model_name: TTS model to use
            language: Language code (e.g., 'de', 'en')
            speaker_wav: Path to reference speaker audio for voice cloning
            use_gpu: Whether to use GPU acceleration
            fallback_to_pyttsx3: Fall back to pyttsx3 if XTTS unavailable
        """
        self.model_name = model_name
        self.language = language
        self.speaker_wav = speaker_wav
        self.use_gpu = use_gpu and torch.cuda.is_available()
        self.fallback_to_pyttsx3 = fallback_to_pyttsx3
        
        self.tts: Optional[TTS] = None
        self.pyttsx3_engine = None
        self.using_fallback = False
        
        self._initialize_engine()

    def _initialize_engine(self) -> None:
        """Initialize the TTS engine (XTTS or fallback)."""
        if XTTS_AVAILABLE:
            try:
                logger.info(f"Initializing XTTS model: {self.model_name}")
                self.tts = TTS(model_name=self.model_name)
                
                if self.use_gpu:
                    self.tts = self.tts.to("cuda")
                    logger.info("XTTS using GPU acceleration")
                else:
                    logger.info("XTTS using CPU")
                
                logger.info("XTTS initialized successfully")
                return
            except Exception as e:
                logger.error(f"Failed to initialize XTTS: {e}")
                if not self.fallback_to_pyttsx3:
                    raise
        
        # Fallback to pyttsx3
        if self.fallback_to_pyttsx3 and PYTTSX3_AVAILABLE:
            logger.warning("XTTS not available, falling back to pyttsx3")
            try:
                self.pyttsx3_engine = pyttsx3.init()
                self._configure_pyttsx3()
                self.using_fallback = True
                logger.info("pyttsx3 fallback initialized")
            except Exception as e:
                logger.error(f"Failed to initialize pyttsx3 fallback: {e}")
                raise RuntimeError("No TTS engine available") from e
        else:
            raise RuntimeError(
                "XTTS not available and fallback disabled or pyttsx3 not installed"
            )

    def _configure_pyttsx3(self) -> None:
        """Configure pyttsx3 engine settings."""
        if not self.pyttsx3_engine:
            return
        
        # Set voice properties
        voices = self.pyttsx3_engine.getProperty('voices')
        
        # Try to find German voice, otherwise use first available
        german_voice = None
        for voice in voices:
            if 'german' in voice.name.lower() or 'de' in voice.languages:
                german_voice = voice
                break
        
        if german_voice:
            self.pyttsx3_engine.setProperty('voice', german_voice.id)
        
        # Set speech rate and volume
        self.pyttsx3_engine.setProperty('rate', 175)  # Speed
        self.pyttsx3_engine.setProperty('volume', 0.9)  # Volume (0.0 to 1.0)

    def synthesize(
        self,
        text: str,
        *,
        output_path: Optional[Union[str, Path]] = None,
        speaker_wav: Optional[Union[str, Path]] = None,
    ) -> Optional[Path]:
        """
        Synthesize speech from text.
        
        Args:
            text: Text to synthesize
            output_path: Where to save audio (temp file if None)
            speaker_wav: Reference speaker audio for voice cloning (overrides init)
            
        Returns:
            Path to generated audio file or None if using pyttsx3 direct playback
        """
        if not text or not text.strip():
            logger.warning("Empty text provided to synthesize")
            return None

        text = text.strip()
        
        if self.using_fallback:
            return self._synthesize_pyttsx3(text, output_path)
        else:
            return self._synthesize_xtts(text, output_path, speaker_wav)

    def _synthesize_xtts(
        self,
        text: str,
        output_path: Optional[Union[str, Path]],
        speaker_wav: Optional[Union[str, Path]],
    ) -> Path:
        """Synthesize using XTTS."""
        if not self.tts:
            raise RuntimeError("XTTS engine not initialized")
        
        # Use provided speaker_wav or fall back to instance default
        speaker = speaker_wav or self.speaker_wav
        
        # Generate temp file if no output path specified
        if output_path is None:
            fd, output_path = tempfile.mkstemp(suffix=".wav", prefix="xtts_")
            os.close(fd)
        
        output_path = Path(output_path)
        
        try:
            logger.debug(f"Synthesizing with XTTS: '{text[:50]}...'")
            
            if speaker:
                # Voice cloning mode
                self.tts.tts_to_file(
                    text=text,
                    file_path=str(output_path),
                    speaker_wav=str(speaker),
                    language=self.language,
                )
            else:
                # Standard synthesis
                self.tts.tts_to_file(
                    text=text,
                    file_path=str(output_path),
                    language=self.language,
                )
            
            logger.info(f"Audio synthesized: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"XTTS synthesis failed: {e}")
            if output_path.exists():
                output_path.unlink()
            raise

    def _synthesize_pyttsx3(
        self,
        text: str,
        output_path: Optional[Union[str, Path]],
    ) -> Optional[Path]:
        """Synthesize using pyttsx3 fallback."""
        if not self.pyttsx3_engine:
            raise RuntimeError("pyttsx3 engine not initialized")
        
        try:
            if output_path:
                # Save to file
                output_path = Path(output_path)
                logger.debug(f"Synthesizing with pyttsx3 to file: {output_path}")
                self.pyttsx3_engine.save_to_file(text, str(output_path))
                self.pyttsx3_engine.runAndWait()
                return output_path
            else:
                # Direct playback
                logger.debug(f"Speaking with pyttsx3: '{text[:50]}...'")
                self.pyttsx3_engine.say(text)
                self.pyttsx3_engine.runAndWait()
                return None
                
        except Exception as e:
            logger.error(f"pyttsx3 synthesis failed: {e}")
            raise

    def speak(self, text: str) -> None:
        """
        Speak text directly without saving to file.
        
        Args:
            text: Text to speak
        """
        if self.using_fallback:
            self._synthesize_pyttsx3(text, None)
        else:
            # XTTS requires file generation, then play
            audio_path = self._synthesize_xtts(text, None, None)
            if audio_path and audio_path.exists():
                # Note: Actual playback would require audio playback library
                # This is placeholder - implement with sounddevice/pyaudio
                logger.info(f"Audio ready for playback: {audio_path}")
                # Clean up temp file
                try:
                    audio_path.unlink()
                except Exception as e:
                    logger.warning(f"Failed to clean up temp file: {e}")

    def is_available(self) -> bool:
        """Check if TTS engine is available."""
        return self.tts is not None or self.pyttsx3_engine is not None

    def get_engine_info(self) -> dict:
        """Get information about the active TTS engine."""
        return {
            "engine": "pyttsx3" if self.using_fallback else "xtts",
            "model": self.model_name if not self.using_fallback else "system",
            "language": self.language,
            "gpu_enabled": self.use_gpu and not self.using_fallback,
            "speaker_cloning": self.speaker_wav is not None,
        }


__all__ = ["XTTSTTS"]
