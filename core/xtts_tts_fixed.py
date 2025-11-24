"""
Text-to-Speech Implementierung mit Windows-eigener Sprachausgabe
"""

import os
import sys
import time
import queue
import threading
import logging
from pathlib import Path
from typing import Optional, Union

try:
    import win32com.client
    WINDOWS_TTS_AVAILABLE = True
except ImportError:
    WINDOWS_TTS_AVAILABLE = False
    import pyttsx3

class XTTSTTS:
    """Text-to-Speech Implementierung mit Windows-eigener Sprachausgabe"""
    
    def __init__(self, voice_clone_path: Optional[Union[str, Path]] = None):
        self.logger = logging.getLogger(__name__)
        self.is_speaking = False
        self.speech_lock = threading.Lock()
        self.voice_clone_path = str(voice_clone_path) if voice_clone_path else None
        self.message_queue = queue.Queue()
        self.stop_event = threading.Event()
        
        try:
            if WINDOWS_TTS_AVAILABLE:
                self.engine = win32com.client.Dispatch("SAPI.SpVoice")
                self.logger.info("Windows TTS-Engine erfolgreich initialisiert")
                
                # Deutsche Stimme auswählen, falls verfügbar
                voices = self.engine.GetVoices()
                for i in range(voices.Count):
                    voice = voices.Item(i)
                    if "german" in voice.GetDescription().lower():
                        self.engine.Voice = voice
                        self.logger.info(f"Deutsche Stimme ausgewählt: {voice.GetDescription()}")
                        break
            else:
                self.engine = pyttsx3.init()
                # Konfiguriere die Stimme
                voices = self.engine.getProperty('voices')
                for voice in voices:
                    if 'german' in voice.languages[0].lower() or 'deu' in voice.languages[0].lower():
                        self.engine.setProperty('voice', voice.id)
                        self.logger.info(f"Deutsche Stimme ausgewählt: {voice.name}")
                        break
                
                self.engine.setProperty('rate', 150)  # Sprechgeschwindigkeit
                self.engine.setProperty('volume', 1.0)  # Lautstärke (0.0 bis 1.0)
                self.logger.info("pyttsx3 als Fallback erfolgreich initialisiert")
                
            # Starte den TTS-Thread
            self.tts_thread = threading.Thread(target=self._tts_worker, daemon=True)
            self.tts_thread.start()
            
        except Exception as e:
            self.logger.error(f"Fehler bei der Initialisierung der TTS-Engine: {e}")
            raise

    def _tts_worker(self):
        """Worker-Thread für die Sprachausgabe"""
        while not self.stop_event.is_set():
            try:
                text = self.message_queue.get(timeout=0.5)
                if text is None:  # Beenden-Signal
                    break
                
                with self.speech_lock:
                    self.is_speaking = True
                    try:
                        if WINDOWS_TTS_AVAILABLE:
                            self.engine.Speak(text, 1)  # 1 = SVSFDefault
                        else:
                            self.engine.say(text)
                            self.engine.runAndWait()
                    except Exception as e:
                        self.logger.error(f"Fehler bei der Sprachsynthese: {e}")
                    finally:
                        self.is_speaking = False
                        
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Fehler im TTS-Thread: {e}")
                self.is_speaking = False
            finally:
                if not self.message_queue.empty():
                    self.message_queue.task_done()

    def speak(self, text: str, language: str = "de", **kwargs) -> bool:
        """Fügt den gegebenen Text der Warteschlange für die Sprachausgabe hinzu"""
        if not text:
            return False
            
        try:
            self.message_queue.put(text)
            return True
        except Exception as e:
            self.logger.error(f"Fehler beim Hinzufügen zur Warteschlange: {e}")
            return False

    def stop_speaking(self) -> None:
        """Stoppt die aktuelle Sprachausgabe und leert die Warteschlange"""
        self.is_speaking = False
        
        try:
            if WINDOWS_TTS_AVAILABLE and hasattr(self, 'engine'):
                self.engine.Speak('', 2)  # 2 = SVSFPurgeBeforeSpeak
            
            # Leere die Warteschlange
            while not self.message_queue.empty():
                try:
                    self.message_queue.get_nowait()
                    self.message_queue.task_done()
                except queue.Empty:
                    break
                    
            self.logger.info("Sprachausgabe gestoppt und Warteschlange geleert")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Stoppen der Sprachausgabe: {e}")

    def is_busy(self) -> bool:
        """Prüft, ob gerade eine Sprachausgabe läuft"""
        if WINDOWS_TTS_AVAILABLE and hasattr(self, 'engine'):
            try:
                if self.is_speaking or not self.message_queue.empty():
                    return True
                if hasattr(self.engine, 'Status'):
                    return self.engine.Status.RunningState == 1  # 1 = SPRS_IS_SPEAKING
            except Exception as e:
                self.logger.warning(f"Fehler beim Überprüfen des TTS-Status: {e}")
        
        return self.is_speaking or not self.message_queue.empty()

    def __del__(self):
        """Aufräumen beim Zerstören des Objekts"""
        try:
            self.stop_speaking()
            self.stop_event.set()
            
            if hasattr(self, 'tts_thread') and self.tts_thread.is_alive():
                self.tts_thread.join(timeout=1.0)
                
            if hasattr(self, 'engine') and not WINDOWS_TTS_AVAILABLE:
                try:
                    self.engine.stop()
                except:
                    pass
                    
        except Exception as e:
            self.logger.warning(f"Fehler beim Aufräumen der TTS-Engine: {e}")

# Beispielverwendung
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    tts = XTTSTTS()
    tts.speak("Hallo, dies ist ein Test der Sprachausgabe.")
    time.sleep(2)  # Warte auf die Sprachausgabe
    tts.speak("Die Sprachausgabe funktioniert einwandfrei.")
    time.sleep(3)  # Warte auf die zweite Sprachausgabe
