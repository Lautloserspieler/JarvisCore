"""
Speech Manager for J.A.R.V.I.S. using XTTS v2 with voice cloning.
Handles text-to-speech synthesis and audio playback.
"""

import os
import threading
import inspect
import importlib
import functools
import warnings
import torch
from typing import Optional
from pathlib import Path

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore", category=UserWarning)

class SpeechManager:
    """
    Manages text-to-speech synthesis using XTTS v2 with voice cloning.
    Handles both file output and audio playback.
    """
    
    def __init__(self,
                 speaker_wav: Optional[str] = None,
                 language: str = "de",
                 prefer_gpu: bool = False,
                 commercial: bool = False):
        """
        Initialize the SpeechManager.
        
        Args:
            speaker_wav: Path to the speaker's voice sample WAV file
            language: Language code (e.g., "de", "en")
            prefer_gpu: Whether to use GPU if available
            commercial: Whether this is for commercial use (requires Coqui license)
        """
        # Set Coqui TOS / license
        os.environ["COQUI_TOS_AGREED"] = "1"
        os.environ["COQUI_COMMERCIAL_LICENSE"] = "1" if commercial else "0"
        
        # Default voice path if not specified
        self.speaker_wav = speaker_wav or str(
            Path(__file__).parent.parent / "models" / "tts" / "voices" / "Jarvis.wav"
        )
        self.language = language
        
        # PyTorch 2.6+ safety: Allow XTTS classes
        self._setup_safe_globals()
        
        # Initialize TTS
        self._init_tts(prefer_gpu)
        
        # For thread safety
        self._lock = threading.Lock()
        
    def _setup_safe_globals(self):
        """Configure PyTorch to allow loading XTTS models."""
        try:
            from TTS.tts.configs.xtts_config import XttsConfig
            torch.serialization.add_safe_globals([XttsConfig])
            xtts_mod = importlib.import_module("TTS.tts.models.xtts")
            allowed = [obj for obj in xtts_mod.__dict__.values() 
                      if inspect.isclass(obj)]
            torch.serialization.add_safe_globals(allowed)
        except Exception as e:
            warnings.warn(f"Could not set up safe globals: {e}")
    
    def _init_tts(self, prefer_gpu: bool):
        """Initialize the TTS model with fallback for weights loading"""
        use_gpu = bool(prefer_gpu and torch.cuda.is_available())
        
        try:
            from TTS.api import TTS
            self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", 
                          gpu=use_gpu)
        except Exception as e:
            if "Weights only load failed" in str(e):
                # Fallback for PyTorch 2.6+ with weights_only restriction
                torch.load = functools.partial(torch.load, weights_only=False)
                from TTS.api import TTS
                self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", 
                              gpu=use_gpu)
            else:
                raise
    
    def save(self, text: str, file_path: Optional[str] = None) -> str:
        """
        Synthesize speech and save to file.
        
        Args:
            text: Text to synthesize
            file_path: Output WAV file path. If None, uses default location.
            
        Returns:
            Path to the generated WAV file
        """
        if not file_path:
            output_dir = Path(__file__).parent.parent / "output"
            output_dir.mkdir(exist_ok=True)
            file_path = str(output_dir / "jarvis_output.wav")
        
        with self._lock:
            self.tts.tts_to_file(
                text=text,
                speaker_wav=self.speaker_wav,
                language=self.language,
                file_path=file_path
            )
        
        return file_path
    
    def say(self, text: str, 
            file_path: Optional[str] = None,
            async_play: bool = True) -> str:
        """
        Synthesize speech and play it.
        
        Args:
            text: Text to speak
            file_path: Optional custom output path
            async_play: Whether to play asynchronously
            
        Returns:
            Path to the generated WAV file
        """
        path = self.save(text, file_path)
        
        try:
            import winsound
            flags = 0x0001  # SND_FILENAME
            if async_play:
                flags |= 0x0001  # SND_ASYNC
            winsound.PlaySound(path, flags)
        except Exception as e:
            warnings.warn(f"Could not play audio: {e}")
        
        return path
    
    def stop(self):
        """Stop any currently playing audio"""
        try:
            import winsound
            winsound.PlaySound(None, 0)  # Stop any playing sound
        except Exception as e:
            warnings.warn(f"Could not stop audio: {e}")
    
    def set_voice(self, speaker_wav: str):
        """Change the voice sample"""
        with self._lock:
            self.speaker_wav = speaker_wav
    
    def set_language(self, language: str):
        """Change the language"""
        with self._lock:
            self.language = language

# Example usage
if __name__ == "__main__":
    # Create a test voice file if it doesn't exist
    test_wav = Path("test_voice.wav")
    if not test_wav.exists():
        import wave
        import struct
        
        # Create a simple silent WAV file
        with wave.open(str(test_wav), 'w') as wf:
            wf.setnchannels(1)  # mono
            wf.setsampwidth(2)   # 2 bytes per sample
            wf.setframerate(22050)
            # 1 second of silence
            wf.writeframes(b'\x00' * 22050 * 2)
    
    # Test the SpeechManager
    sm = SpeechManager(speaker_wav=str(test_wav))
    print("Saving test audio to output/...")
    sm.save("This is a test of the speech manager.")
    print("Playing test audio...")
    sm.say("Hello! This is J.A.R.V.I.S. speaking.")
    input("Press Enter to exit...")
