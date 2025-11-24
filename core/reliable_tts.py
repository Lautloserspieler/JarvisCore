"""
Reliable TTS implementation using pyttsx3 with better error handling
"""

import os
import queue
import threading
import time
from pathlib import Path
from typing import Optional, Union
from utils.logger import Logger

class ReliableTTS:
    """Reliable Text-to-Speech with fallback mechanisms"""
    
    def __init__(self):
        self.logger = Logger()
        self.is_speaking = False
        self.speech_lock = threading.Lock()
        self.message_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.engine = None
        
        # Initialize the TTS engine
        self._init_engine()
        
        # Start the TTS thread
        self.tts_thread = threading.Thread(target=self._tts_worker, daemon=True)
        self.tts_thread.start()
    
    def _init_engine(self):
        """Initialize the TTS engine with fallbacks"""
        try:
            import pyttsx3
            
            # First try with default initialization
            self.engine = pyttsx3.init()
            
            # Configure voice settings
            try:
                # Try to find a German voice
                voices = self.engine.getProperty('voices')
                if voices:
                    # Look for German voices first
                    for voice in voices:
                        if 'german' in (voice.languages[0] if voice.languages else '').lower():
                            self.engine.setProperty('voice', voice.id)
                            self.logger.info(f"Using German voice: {voice.name}")
                            break
                    else:
                        # No German voice found, use the first available
                        if voices:
                            self.engine.setProperty('voice', voices[0].id)
                            self.logger.info(f"Using default voice: {voices[0].name}")
                
                # Set rate and volume
                self.engine.setProperty('rate', 150)  # Words per minute
                self.engine.setProperty('volume', 1.0)  # 0.0 to 1.0
                
                # Test the engine
                self.engine.say("")
                self.engine.runAndWait()
                
                self.logger.info("TTS engine initialized successfully")
                
            except Exception as e:
                self.logger.error(f"Error configuring TTS: {e}")
                # Try to reinitialize as a fallback
                self.engine = pyttsx3.init()
                
        except Exception as e:
            self.logger.error(f"Failed to initialize TTS engine: {e}")
            self.engine = None
    
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
                        if self.engine:
                            self.engine.say(text)
                            self.engine.runAndWait()
                        else:
                            self.logger.warning("TTS engine not available")
                            # Try to reinitialize the engine if it failed
                            self._init_engine()
                    except Exception as e:
                        self.logger.error(f"Error in TTS: {e}")
                        # Try to reinitialize the engine on error
                        self._init_engine()
                    finally:
                        self.is_speaking = False
                        self.message_queue.task_done()
            
            except queue.Empty:
                # Keep the thread alive but don't consume CPU
                time.sleep(0.1)
                continue
            except Exception as e:
                self.logger.error(f"Error in TTS worker: {e}")
                time.sleep(1)  # Prevent tight loop on errors
    
    def speak(self, text: str, block: bool = False) -> bool:
        """
        Speak the given text
        
        Args:
            text: Text to speak
            block: If True, block until speech is complete
            
        Returns:
            bool: True if text was queued successfully
        """
        if not text:
            return False
            
        # Ensure the engine is initialized
        if not self.engine:
            self._init_engine()
            if not self.engine:
                self.logger.error("TTS engine could not be initialized")
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
        if self.engine:
            self.engine.stop()
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
        """Cleanup resources"""
        try:
            self.stop_event.set()
            if hasattr(self, 'tts_thread') and self.tts_thread.is_alive():
                self.tts_thread.join(timeout=2.0)
            if hasattr(self, 'engine'):
                self.engine.stop()
        except Exception as e:
            # Safely handle cases where logger might not be available
            try:
                if hasattr(self, 'logger'):
                    self.logger.warning(f"Error during TTS cleanup: {e}")
                else:
                    print(f"Error during TTS cleanup: {e}")
            except:
                pass

# Example usage
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    tts = ReliableTTS()
    tts.speak("Hallo, dies ist ein Test der deutschen Sprachsynthese.")
    
    # Keep the script running
    try:
        while tts.is_busy():
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
