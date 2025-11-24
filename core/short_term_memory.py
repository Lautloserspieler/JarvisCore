"""
Kurzzeitgedächtnis für J.A.R.V.I.S.
Verwaltet den Kontext des aktuellen Gesprächs und kürzliche Interaktionen.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import uuid

logger = logging.getLogger(__name__)

class ShortTermMemory:
    """Verwaltet das Kurzzeitgedächtnis für die aktuelle Konversation.
    
    Features:
    - Verfolgung von Gesprächsthemen
    - Kontextverwaltung für natürlich klingende Unterhaltungen
    - Unterstützung für Rückfragen und Anschlussfragen
    """
    
    def __init__(self, max_context_length: int = 15, max_context_age_minutes: int = 120):
        """Initialisiert das Kurzzeitgedächtnis.
        
        Args:
            max_context_length: Maximale Anzahl von Kontexteinträgen
            max_context_age_minutes: Maximale Alter eines Kontexteintrags in Minuten
        """
        self.max_context_length = max_context_length
        self.max_context_age = timedelta(minutes=max_context_age_minutes)
        self.conversation_context: List[Dict[str, Any]] = []
        self.current_topics = set()  # Aktive Themen im aktuellen Gespräch
        self.last_activity = datetime.now()
        
    def add_context(self, role: str, content: str, timestamp: Optional[datetime] = None, 
                   topics: Optional[List[str]] = None) -> None:
        """Fügt einen neuen Kontexteintrag hinzu.
        
        Args:
            role: Rolle des Sprechers ('user' oder 'assistant')
            content: Inhalt der Nachricht
            timestamp: Optionaler Zeitstempel (default: aktuelle Zeit)
            topics: Liste von Themen, die in dieser Nachricht vorkommen
        """
        if timestamp is None:
            timestamp = datetime.now()
            
        entry = {
            'id': str(uuid.uuid4()),
            'role': role,
            'content': content,
            'timestamp': timestamp,
            'topics': set(topics) if topics else set()
        }
        
        self.conversation_context.append(entry)
        self.last_activity = timestamp
        
        # Themen aktualisieren
        if topics:
            self.current_topics.update(topics)
        
        # Automatische Themenerkennung für Benutzernachrichten
        if role == 'user' and not topics:
            detected_topics = self._detect_topics(content)
            if detected_topics:
                entry['topics'].update(detected_topics)
                self.current_topics.update(detected_topics)
        
        # Alte Einträge aufräumen
        self._cleanup()
    
    def get_recent_context(self, max_items: int = 5) -> List[Dict[str, Any]]:
        """Gibt den aktuellen Kontext zurück.
        
        Args:
            max_items: Maximale Anzahl zurückzugebender Einträge
            
        Returns:
            Liste der neuesten Kontexteinträge
        """
        self._cleanup()
        return self.conversation_context[-max_items:]
    
    def clear_context(self) -> None:
        """Löscht den gesamten Kontext."""
        self.conversation_context = []
    
    def _cleanup(self) -> None:
        """Entfernt alte Einträge und begrenzt die Größe des Kontexts."""
        now = datetime.now()
        
        # Entferne veraltete Einträge
        self.conversation_context = [
            entry for entry in self.conversation_context
            if now - entry['timestamp'] <= self.max_context_age
        ]
        
        # Begrenze die Anzahl der Einträge
        if len(self.conversation_context) > self.max_context_length:
            self.conversation_context = self.conversation_context[-self.max_context_length:]
    
    def get_conversation_summary(self, include_topics: bool = True) -> str:
        """Erstellt eine Zusammenfassung der aktuellen Konversation.
        
        Args:
            include_topics: Ob Themeninformationen eingeschlossen werden sollen
            
        Returns:
            Zusammenfassung als String
        """
        self._cleanup()
        if not self.conversation_context:
            return "Kein aktueller Kontext verfügbar."
            
        summary = []
        
        # Aktive Themen einfügen, falls gewünscht
        if include_topics and self.current_topics:
            topics_str = ", ".join(sorted(self.current_topics))
            summary.append(f"Aktuelle Themen: {topics_str}")
            summary.append("-" * 40)
            
        # Konversationsverlauf
        for entry in self.conversation_context[-5:]:  # Nur die letzten 5 Einträge
            speaker = "Nutzer" if entry['role'] == 'user' else "Assistent"
            time_str = entry['timestamp'].strftime('%H:%M')
            
            # Themen der Nachricht anzeigen, falls vorhanden
            topics_info = ""
            if include_topics and entry.get('topics'):
                topics_info = f" [Themen: {', '.join(entry['topics'])}]"
                
            summary.append(f"[{time_str}] {speaker}: {entry['content']}{topics_info}")
            
        return "\n".join(summary)
        
    def _detect_topics(self, text: str) -> List[str]:
        """Erkennt Themen in einem Text.
        
        Args:
            text: Der zu analysierende Text
            
        Returns:
            Liste der erkannten Themen
        """
        # Einfache Themenerkennung - kann später durch NLP erweitert werden
        topics = []
        text_lower = text.lower()
        
        # Beispielthemen (kann erweitert werden)
        topic_keywords = {
            'projekt': ['projekt', 'aufgabe', 'todo', 'task'],
            'erinnerung': ['erinner', 'daran denken', 'nicht vergessen'],
            'termin': ['termin', 'kalender', 'treffen', 'meeting'],
            'frage': ['warum', 'wie', 'was', 'wo', 'wann', 'wer', 'wem', 'wessen']
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                topics.append(topic)
                
        return topics
    
    def get_last_interaction_time(self) -> Optional[datetime]:
        """Gibt den Zeitpunkt der letzten Interaktion zurück.
        
        Returns:
            Zeitstempel der letzten Interaktion oder None, falls keine vorhanden
        """
        if not self.conversation_context:
            return None
        return self.conversation_context[-1]['timestamp']
