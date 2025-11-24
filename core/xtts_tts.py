"""
Text-to-Speech Implementierung für J.A.R.V.I.S.
Verwendet die Windows-eigene Sprachausgabe für maximale Kompatibilität
"""

import os
import threading
import queue
import time
from typing import Optional, Union
from pathlib import Path
from utils.logger import Logger

# Versuche, die Windows-Sprachausgabe zu importieren
try:
    import win32com.client
    WINDOWS_TTS_AVAILABLE = True
except ImportError:
    WINDOWS_TTS_AVAILABLE = False
    import warnings
    warnings.warn("win32com.client nicht verfügbar. Installiere mit: pip install pywin32")

class XTTSTTS:
    """Text-to-Speech Implementierung mit Windows-eigener Sprachausgabe"""
    
    def __init__(self, voice_clone_path: Optional[Union[str, Path]] = None):
        self.logger = Logger()
        self.is_speaking = False
        self.speech_lock = threading.Lock()
        self.voice_clone_path = str(voice_clone_path) if voice_clone_path else None
        self.message_queue = queue.Queue()
        self.stop_event = threading.Event()
        
        try:
            if WINDOWS_TTS_AVAILABLE:
                self.engine = win32com.client.Dispatch("SAPI.SpVoice")
                self.logger.info("Windows TTS-Engine erfolgreich initialisiert")
                
                # Starte den TTS-Thread
                self.tts_thread = threading.Thread(target=self._tts_worker, daemon=True)
                self.tts_thread.start()
            else:
                raise ImportError("Windows TTS ist nicht verfügbar. Installiere pywin32 mit: pip install pywin32")
                
        except Exception as e:
            self.logger.error(f"Fehler bei der Initialisierung der TTS-Engine: {e}")
            raise
    
    def _tts_worker(self):
        """Worker-Thread für die Sprachausgabe"""
        self.logger.info("TTS Worker-Thread gestartet")
        while not self.stop_event.is_set():
            try:
                text = self.message_queue.get(timeout=0.5)
                if text is None:  # Beenden-Signal
                    self.logger.info("Beenden-Signal empfangen, beende TTS Worker-Thread")
                    break
                
                self.logger.info(f"Verarbeite TTS-Nachricht: {text[:100]}...")
                self.is_speaking = True
                
                try:
                    # Führe die Sprachausgabe aus
                    self.logger.debug("Starte Sprachsynthese...")
                    if WINDOWS_TTS_AVAILABLE:
                        self.engine.Speak(text, 0)  # 0 = SVSFlagsAsync
                    else:
                        self.logger.error("Windows TTS ist nicht verfügbar")
                    
                    self.logger.debug("Sprachsynthese abgeschlossen")
                    
                except Exception as e:
                    self.logger.error(f"Fehler bei der Sprachsynthese: {e}")
                
                # Warte kurz, bevor die nächste Nachricht verarbeitet wird
                time.sleep(0.1)
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Unbehandelter Fehler im TTS-Thread: {e}")
            finally:
                self.is_speaking = False
                self.message_queue.task_done()
                
        self.logger.info("TTS Worker-Thread wird beendet")
    
    def speak(self, text: str, language: str = "de", **kwargs) -> bool:
        """Fügt den gegebenen Text der Warteschlange für die Sprachausgabe hinzu
        
        Args:
            text: Der zu sprechende Text
            language: Die Sprache des Textes (z.B. 'de' für Deutsch, 'en' für Englisch)
            
        Returns:
            bool: True, wenn der Text erfolgreich zur Warteschlange hinzugefügt wurde, sonst False
        """
        if not text:
            return False
            
        try:
            # Wenn keine Windows-TTS verfüg ist, versuche es mit pyttsx3 als Fallback
            if not WINDOWS_TTS_AVAILABLE and not hasattr(self, '_pyttsx3_warning_shown'):
                self.logger.warning("Windows TTS nicht verfügbar, versuche pyttsx3 als Fallback")
                try:
                    import pyttsx3
                    self.engine = pyttsx3.init()
                    self.engine.setProperty('rate', 150)
                    self.engine.setProperty('volume', 1.0)
                    self.logger.info("pyttsx3 als Fallback erfolgreich initialisiert")
                except Exception as e:
                    self.logger.error(f"Konnte pyttsx3 nicht als Fallback initialisieren: {e}")
                    return False
                self._pyttsx3_warning_shown = True
                
            self.message_queue.put(text)
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Hinzufügen zur Warteschlange: {e}")
            return False
    
    def is_busy(self) -> bool:
        """Prüft, ob gerade eine Sprachausgabe läuft
        
        Returns:
            bool: True, wenn gerade eine Sprachausgabe aktiv ist oder Nachrichten in der Warteschlange sind
        """
        if WINDOWS_TTS_AVAILABLE and hasattr(self, 'engine'):
            # Prüfe den Status der Windows-TTS-Engine
            try:
                # Wenn die Engine gerade spricht, ist sie beschäftigt
                if self.is_speaking or not self.message_queue.empty():
                    return True
                
                # Zusätzliche Prüfung für Windows-TTS
                if hasattr(self.engine, 'Status'):
                    return self.engine.Status.RunningState == 1  # 1 = SPRS_IS_SPEAKING
            except Exception as e:
                self.logger.warning(f"Fehler beim Überprüfen des TTS-Status: {e}")
        
        # Fallback: Verwende die einfache Prüfung
        return self.is_speaking or not self.message_queue.empty()
    
    def stop_speaking(self) -> None:
        """Stoppt die aktuelle Sprachausgabe und leert die Warteschlange"""
        self.is_speaking = False
        
        try:
            # Versuche, die aktuelle Wiedergabe zu stoppen
            if WINDOWS_TTS_AVAILABLE and hasattr(self, 'engine'):
                self.engine.Speak('', 2)  # 2 = SVSFPurgeBeforeSpeak
            
            # Leere die Warteschlange
            with self.message_queue.mutex:
                self.message_queue.queue.clear()
                
            self.logger.info("Sprachausgabe gestoppt und Warteschlange geleert")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Stoppen der Sprachausgabe: {e}")
    
    def __del__(self):
        """Aufräumen beim Zerstören des Objekts"""
        try:
            self.stop_speaking()
            self.stop_event.set()
            
            if hasattr(self, 'tts_thread') and self.tts_thread.is_alive():
                self.tts_thread.join(timeout=1.0)
                
            # Schließe die TTS-Engine
            if hasattr(self, 'engine'):
                if WINDOWS_TTS_AVAILABLE:
                    # Windows-TTS muss nicht explizit geschlossen werden
                    pass
                else:
                    # pyttsx3-Engine stoppen
                    try:
                        self.engine.stop()
                    except:
                        pass
                        
        except Exception as e:
            self.logger.warning(f"Fehler beim Aufräumen der TTS-Engine: {e}")
