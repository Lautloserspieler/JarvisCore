"""
Simple TTS implementation using Coqui TTS with fallback to pyttsx3
"""

import os
import queue
import threading
import time
from pathlib import Path
from typing import Optional, Union
import torch
from utils.logger import Logger

class SimpleTTS:
    """Simple Text-to-Speech with voice cloning support"""
    
    def __init__(self):
        self.logger = Logger()
        self.is_speaking = False
        self.speech_lock = threading.Lock()
        self.message_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tts = None
        
        try:
            # Try to import TTS
            from TTS.api import TTS
            
            # Initialize TTS with a smaller model
            self.tts = TTS("tts_models/de/thorsten/tacotron2-DDC").to(self.device)
            self.logger.info("Initialized Coqui TTS with German voice")
            
        except Exception as e:
            self.logger.warning(f"Could not initialize Coqui TTS: {e}")
            self._init_pyttsx3()
        
        # Start the TTS thread
        self.tts_thread = threading.Thread(target=self._tts_worker, daemon=True)
        self.tts_thread.start()
    
    def _init_pyttsx3(self):
        """Fallback to pyttsx3 if Coqui TTS is not available"""
        try:
            import pyttsx3
            self.tts = pyttsx3.init()
            # Configure voice
            voices = self.tts.getProperty('voices')
            for voice in voices:
                if 'german' in voice.languages[0].lower() or 'deu' in voice.languages[0].lower():
                    self.tts.setProperty('voice', voice.id)
                    break
            self.tts.setProperty('rate', 150)
            self.logger.info("Initialized pyttsx3 as fallback")
        except Exception as e:
            self.logger.error(f"Could not initialize pyttsx3: {e}")
    
    def _tts_worker(self):
        """Worker thread for TTS processing"""
        while not self.stop_event.is_set():
            try:
                text = self.message_queue.get(timeout=0.5)
                if text is None:  # Shutdown signal
                    break
                
                with self.speech_lock:
                    self.is_speaking = True
                    try:
                        self._speak(text)
                    except Exception as e:
                        self.logger.error(f"Error in TTS: {e}")
                    finally:
                        self.is_speaking = False
                        self.message_queue.task_done()
            
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error in TTS worker: {e}")
    
    def _speak(self, text: str):
        """Internal method to speak text"""
        if not text or not self.tts:
            return
        
        try:
            if hasattr(self.tts, 'tts_to_file'):
                # Coqui TTS
                self.tts.tts_to_file(
                    text=text,
                    file_path="temp_output.wav"
                )
                self._play_audio("temp_output.wav")
            else:
                # pyttsx3 fallback
                self.tts.say(text)
                self.tts.runAndWait()
                
        except Exception as e:
            self.logger.error(f"Error in speech synthesis: {e}")
    
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
    
    def speak(self, text: str, **kwargs) -> bool:
        """Add text to the TTS queue"""
        if not text or not self.tts:
            return False
            
        try:
            self.message_queue.put(text)
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
    
    tts = SimpleTTS()
    tts.speak("Hallo, dies ist ein Test der deutschen Sprachsynthese.")
    
    # Keep the script running
    try:
        while tts.is_busy():
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
