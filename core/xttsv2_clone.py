"""
XTTSv2 Implementation with Voice Cloning
"""

import os
import queue
import threading
import time
import torch
from pathlib import Path
from typing import Optional, Union
from utils.logger import Logger

class XTTSv2Clone:
    """XTTSv2 with Voice Cloning"""
    
    def __init__(self, model_name: str = "tts_models/multilingual/multi-dataset/xtts_v2"):
        self.logger = Logger()
        self.is_speaking = False
        self.speech_lock = threading.Lock()
        self.message_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.model_name = model_name
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        try:
            self._load_model()
            # Start the TTS thread
            self.tts_thread = threading.Thread(target=self._tts_worker, daemon=True)
            self.tts_thread.start()
        except Exception as e:
            self.logger.error(f"Failed to initialize XTTSv2: {e}")
            raise
    
    def _load_model(self):
        """Load the XTTSv2 model"""
        try:
            from TTS.api import TTS
            
            self.logger.info(f"Loading XTTSv2 model: {self.model_name}")
            self.model = TTS(self.model_name).to(self.device)
            self.logger.info("XTTSv2 model loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Error loading XTTSv2 model: {e}")
            raise
    
    def _tts_worker(self):
        """Worker thread for TTS processing"""
        while not self.stop_event.is_set():
            try:
                # Get text, voice file, and language from queue
                try:
                    data = self.message_queue.get(timeout=0.5)
                    if data is None:  # Shutdown signal
                        break
                    
                    text, voice_file, language = data
                except queue.Empty:
                    continue
                
                with self.speech_lock:
                    self.is_speaking = True
                    try:
                        self._synthesize(text, voice_file, language)
                    except Exception as e:
                        self.logger.error(f"Error in TTS synthesis: {e}")
                    finally:
                        self.is_speaking = False
                        self.message_queue.task_done()
            
            except Exception as e:
                self.logger.error(f"Error in TTS worker: {e}")
    
    def _synthesize(self, text: str, voice_file: str, language: str):
        """Synthesize speech with voice cloning"""
        if not self.model:
            self.logger.error("Model not loaded")
            return
            
        try:
            output_file = "output_tts.wav"
            
            # Generate speech with voice cloning
            self.model.tts_to_file(
                text=text,
                file_path=output_file,
                speaker_wav=voice_file,
                language=language
            )
            
            # Play the generated audio
            self._play_audio(output_file)
            
        except Exception as e:
            self.logger.error(f"Error in speech synthesis: {e}")
            raise
    
    def _play_audio(self, file_path: str):
        """Play audio file using sounddevice"""
        try:
            import sounddevice as sd
            import soundfile as sf
            
            data, sample_rate = sf.read(file_path, dtype='float32')
            sd.play(data, sample_rate)
            sd.wait()
            
        except Exception as e:
            self.logger.error(f"Error playing audio: {e}")
    
    def speak(self, text: str, voice_file: str, language: str = "en") -> bool:
        """Add text to the TTS queue with voice cloning"""
        if not text or not self.model:
            return False
            
        try:
            if not os.path.exists(voice_file):
                self.logger.error(f"Voice file not found: {voice_file}")
                return False
                
            self.message_queue.put((text, voice_file, language))
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding to TTS queue: {e}")
            return False
    
    def stop_speaking(self) -> None:
        """Stop current speech and clear queue"""
        self.is_speaking = False
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
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Example usage
    tts = XTTSv2Clone()
    
    # Replace with your voice sample
    voice_sample = "path/to/your/voice_sample.wav"
    
    if os.path.exists(voice_sample):
        tts.speak(
            text="This is a test of the XTTSv2 voice cloning system.",
            voice_file=voice_sample,
            language="en"
        )
        
        # Keep the script running
        try:
            while tts.is_busy():
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass
    else:
        print(f"Voice sample not found: {voice_sample}")
