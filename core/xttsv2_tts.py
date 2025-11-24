"""
XTTSv2 Implementation with Voice Cloning
Based on Coqui TTS XTTSv2 model
"""

import os
import torch
import torchaudio
import numpy as np
import queue
import threading
import time
from pathlib import Path
from typing import Optional, Union
from TTS.api import TTS
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts
from utils.logger import Logger

class XTTSv2TTS:
    """XTTSv2 Text-to-Speech with Voice Cloning"""
    
    def __init__(self, model_name: str = "tts_models/multilingual/multi-dataset/xtts_v2", 
                 device: str = "cuda" if torch.cuda.is_available() else "cpu"):
        self.logger = Logger()
        self.device = device
        self.is_speaking = False
        self.speech_lock = threading.Lock()
        self.message_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.model = None
        self.speaker_wav = None
        self.language = "de"
        
        try:
            self.logger.info(f"Initializing XTTSv2 on device: {self.device}")
            
            # Initialize TTS
            self.model = TTS(model_name).to(device)
            
            # Start the TTS worker thread
            self.tts_thread = threading.Thread(target=self._tts_worker, daemon=True)
            self.tts_thread.start()
            
            self.logger.info("XTTSv2 initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize XTTSv2: {e}")
            raise
    
    def set_voice(self, speaker_wav: Union[str, Path], language: str = "de") -> None:
        """Set the voice clone and language"""
        if not os.path.exists(speaker_wav):
            self.logger.warning(f"Speaker file not found: {speaker_wav}")
            return
            
        self.speaker_wav = str(speaker_wav)
        self.language = language
        self.logger.info(f"Voice clone set to: {self.speaker_wav}, language: {self.language}")
    
    def _tts_worker(self):
        """Worker thread for TTS processing"""
        while not self.stop_event.is_set():
            try:
                # Get text from queue with timeout
                try:
                    text = self.message_queue.get(timeout=0.5)
                except queue.Empty:
                    continue
                    
                if text is None:  # Shutdown signal
                    break
                    
                with self.speech_lock:
                    self.is_speaking = True
                    try:
                        # Generate speech
                        if self.speaker_wav and os.path.exists(self.speaker_wav):
                            # Use voice cloning
                            self.model.tts_to_file(
                                text=text,
                                speaker_wav=self.speaker_wav,
                                language=self.language,
                                file_path="temp_output.wav"
                            )
                            
                            # Play the generated audio
                            self._play_audio("temp_output.wav")
                        else:
                            self.logger.warning("No voice clone set, using default voice")
                            self.model.tts_to_file(
                                text=text,
                                language=self.language,
                                file_path="temp_output.wav"
                            )
                            self._play_audio("temp_output.wav")
                            
                    except Exception as e:
                        self.logger.error(f"Error in TTS generation: {e}")
                        
                    finally:
                        self.is_speaking = False
                        self.message_queue.task_done()
            
            except Exception as e:
                self.logger.error(f"Error in TTS worker: {e}")
                self.is_speaking = False
    
    def _play_audio(self, file_path: str) -> None:
        """Play generated audio file"""
        try:
            # Use sounddevice for cross-platform audio playback
            import sounddevice as sd
            import soundfile as sf
            
            # Load audio file
            data, sample_rate = sf.read(file_path, dtype='float32')
            
            # Play audio
            sd.play(data, sample_rate)
            sd.wait()  # Wait until audio is done playing
            
        except Exception as e:
            self.logger.error(f"Error playing audio: {e}")
    
    def speak(self, text: str, language: Optional[str] = None, **kwargs) -> bool:
        """Add text to the TTS queue for speech synthesis"""
        if not text or not self.model:
            return False
            
        try:
            # Update language if provided
            if language:
                self.language = language
                
            self.message_queue.put(text)
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding text to TTS queue: {e}")
            return False
    
    def stop_speaking(self) -> None:
        """Stop current speech and clear queue"""
        self.is_speaking = False
        
        # Clear the queue
        while not self.message_queue.empty():
            try:
                self.message_queue.get_nowait()
                self.message_queue.task_done()
            except queue.Empty:
                break
    
    def is_busy(self) -> bool:
        """Check if TTS is currently speaking"""
        return self.is_speaking or not self.message_queue.empty()
    
    def __del__(self):
        """Cleanup on object destruction"""
        try:
            self.stop_speaking()
            self.stop_event.set()
            
            if hasattr(self, 'tts_thread') and self.tts_thread.is_alive():
                self.tts_thread.join(timeout=1.0)
                
        except Exception as e:
            self.logger.warning(f"Error during TTS cleanup: {e}")

# Example usage
if __name__ == "__main__":
    # Initialize TTS with voice cloning
    tts = XTTSv2TTS()
    
    # Set voice clone (path to a WAV file with the target voice)
    tts.set_voice("path/to/voice_sample.wav")
    
    # Test speech
    tts.speak("Hallo, dies ist ein Test der XTTSv2 Sprachsynthese mit Stimmklon.")
    
    # Wait for speech to finish
    while tts.is_busy():
        time.sleep(0.1)
