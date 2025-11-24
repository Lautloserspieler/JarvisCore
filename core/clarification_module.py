"""
Modul zur Klärung unklarer Befehle
Ermöglicht Rückfragen, wenn ein Befehl nicht eindeutig ist.
"""

from typing import List, Dict, Any, Optional, Tuple
import random
import logging

logger = logging.getLogger(__name__)

class ClarificationModule:
    """Verwaltet die Klärung unklarer Befehle."""
    
    def __init__(self, max_clarification_attempts: int = 2):
        """Initialisiert das Klärungsmodul.
        
        Args:
            max_clarification_attempts: Maximale Anzahl von Rückfragen pro unklarem Befehl
        """
        self.max_attempts = max_clarification_attempts
        self.clarification_attempts: Dict[str, int] = {}
        self.pending_commands: Dict[str, Dict[str, Any]] = {}
        
        # Mögliche Rückfragen bei Unklarheiten
        self.clarification_phrases = [
            "Könnten Sie das genauer erläutern?",
            "Ich bin mir nicht sicher, was Sie meinen. Können Sie das präzisieren?",
            "Das habe ich nicht ganz verstanden. Meinten Sie vielleicht...?",
            "Könnten Sie das bitte anders formulieren?",
            "Ich brauche etwas mehr Kontext, um Ihnen besser zu helfen."
        ]
    
    def needs_clarification(self, command_id: str, command: str, context: List[Dict[str, Any]]) -> Tuple[bool, Optional[str]]:
        """Bestimmt, ob ein Befehl geklaert werden muss."""

        trimmed = command.strip()
        if len(trimmed) < 3:
            return True, "Der Befehl wirkt unvollstaendig. Bitte fuehren Sie ihn genauer aus."

        words = trimmed.lower().split()
        vague_indicators = {"das", "es", "dies", "jenes", "irgendwas"}
        pronoun_hits = [word for word in words if word in vague_indicators]
        if pronoun_hits:
            meaningful = set(words) - vague_indicators - {"ein", "eine", "einen", "der", "die", "den", "dem", "denn", "auf", "mit", "und", "zu", "zum", "zur", "ist", "sind"}
            trailing_hits = all(words.index(hit) >= len(words) - 2 for hit in pronoun_hits)
            if len(words) <= 6 or not meaningful or trailing_hits:
                return True, "Auf was genau bezieht sich 'das'? Koennen Sie das bitte genauer spezifizieren?"

        if command_id in self.clarification_attempts:
            if self.clarification_attempts[command_id] >= self.max_attempts:
                return False, "Ich habe Schwierigkeiten, den Befehl zu verstehen. Bitte formulieren Sie ihn anders."

            self.clarification_attempts[command_id] += 1

            if self.clarification_attempts[command_id] > 1:
                return True, "Entschuldigung, ich verstehe es immer noch nicht genau. Koennen Sie es anders formulieren?"

        return False, None

    def get_clarification_prompt(self, command: str, context: List[Dict[str, Any]]) -> str:
        """Generiert eine Rückfrage zur Klärung eines unklaren Befehls.
        
        Args:
            command: Der unklare Befehl
            context: Aktueller Kontext der Konversation
            
        Returns:
            Rückfrage als String
        """
        # Wähle eine zufällige Rückfrage aus
        return random.choice(self.clarification_phrases)
    
    def store_pending_command(self, command_id: str, command: str, context: Dict[str, Any]) -> None:
        """Speichert einen Befehl, der auf Klärung wartet.
        
        Args:
            command_id: Eindeutige ID des Befehls
            command: Der unklare Befehl
            context: Zusätzlicher Kontext
        """
        self.pending_commands[command_id] = {
            'command': command,
            'context': context,
            'timestamp': context.get('timestamp')
        }
        
        # Initialisiere den Zähler für diesen Befehl
        self.clarification_attempts[command_id] = 1
    
    def get_pending_command(self, command_id: str) -> Optional[Dict[str, Any]]:
        """Holt einen gespeicherten Befehl.
        
        Args:
            command_id: Eindeutige ID des Befehls
            
        Returns:
            Der gespeicherte Befehl mit Kontext oder None
        """
        return self.pending_commands.pop(command_id, None)
    
    def clear_pending_command(self, command_id: str) -> None:
        """Entfernt einen gespeicherten Befehl.
        
        Args:
            command_id: Eindeutige ID des Befehls
        """
        if command_id in self.pending_commands:
            del self.pending_commands[command_id]
        if command_id in self.clarification_attempts:
            del self.clarification_attempts[command_id]
    
    def get_remaining_attempts(self, command_id: str) -> int:
        """Gibt die verbleibenden Klärungsversuche zurück.
        
        Args:
            command_id: Eindeutige ID des Befehls
            
        Returns:
            Anzahl der verbleibenden Versuche
        """
        if command_id not in self.clarification_attempts:
            return self.max_attempts
        return max(0, self.max_attempts - self.clarification_attempts[command_id])
