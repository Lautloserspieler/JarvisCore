"""Notes Plugin for JARVIS - Schnelle Notizen"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

# Plugin Metadata
PLUGIN_NAME = "Notizen"
PLUGIN_DESCRIPTION = "Erstellt und verwaltet schnelle Notizen"
PLUGIN_VERSION = "1.0.0"
PLUGIN_AUTHOR = "Lautloserspieler"


class NotesPlugin:
    """Plugin für Notizen-Verwaltung"""
    
    def __init__(self):
        self.data_dir = Path("data/notes")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.notes_file = self.data_dir / "notes.json"
        self.notes = self._load_notes()
        
    def process(self, command: str, context: Dict[str, Any]) -> Optional[str]:
        """
        Verarbeitet Notizen-Befehle
        
        Beispiele:
        - "Notiere: Meeting um 14 Uhr"
        - "Neue Notiz: Milch kaufen"
        - "Zeige alle Notizen"
        - "Zeige letzte 5 Notizen"
        - "Suche Notizen nach Meeting"
        - "Lösche Notiz 3"
        - "Lösche alle Notizen"
        """
        command_lower = command.lower()
        
        # Neue Notiz erstellen
        if any(word in command_lower for word in ["notier", "neue notiz", "notiz:"]):
            return self._create_note(command)
        
        # Notizen anzeigen
        elif "zeige" in command_lower or "liste" in command_lower:
            return self._show_notes(command_lower)
        
        # Notizen suchen
        elif "such" in command_lower or "finde" in command_lower:
            return self._search_notes(command_lower)
        
        # Notiz löschen
        elif "lösch" in command_lower or "entfern" in command_lower:
            return self._delete_note(command_lower)
        
        # Export
        elif "export" in command_lower:
            return self._export_notes()
        
        return None
    
    def _load_notes(self) -> List[Dict[str, Any]]:
        """Lädt Notizen aus Datei"""
        if not self.notes_file.exists():
            return []
        
        try:
            with open(self.notes_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Fehler beim Laden der Notizen: {e}")
            return []
    
    def _save_notes(self):
        """Speichert Notizen in Datei"""
        try:
            with open(self.notes_file, 'w', encoding='utf-8') as f:
                json.dump(self.notes, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Fehler beim Speichern der Notizen: {e}")
    
    def _create_note(self, command: str) -> str:
        """Erstellt neue Notiz"""
        # Extrahiere Notiz-Text
        content = self._extract_note_content(command)
        
        if not content:
            return "❌ Keine Notiz-Inhalt gefunden. Beispiel: 'Notiere: Text hier'"
        
        # Neue Notiz erstellen
        note = {
            "id": len(self.notes) + 1,
            "content": content,
            "created_at": datetime.now().isoformat(),
            "tags": self._extract_tags(content)
        }
        
        self.notes.append(note)
        self._save_notes()
        
        return f"✅ Notiz #{note['id']} erstellt: {content[:50]}{'...' if len(content) > 50 else ''}"
    
    def _show_notes(self, command: str) -> str:
        """Zeigt Notizen an"""
        if not self.notes:
            return "ℹ️ Keine Notizen vorhanden."
        
        # Anzahl extrahieren ("letzte 5 Notizen")
        limit = self._extract_number(command)
        if not limit:
            limit = 10  # Default: 10 neueste
        
        # Zeige neueste zuerst
        recent_notes = self.notes[-limit:]
        recent_notes.reverse()
        
        result = f"📝 Deine Notizen (letzte {len(recent_notes)}):\n\n"
        
        for note in recent_notes:
            date = datetime.fromisoformat(note["created_at"]).strftime("%d.%m.%Y %H:%M")
            content = note["content"][:80] + "..." if len(note["content"]) > 80 else note["content"]
            result += f"#{note['id']} | {date}\n"
            result += f"   {content}\n"
            if note.get("tags"):
                result += f"   🏷️ {', '.join(note['tags'])}\n"
            result += "\n"
        
        return result.strip()
    
    def _search_notes(self, command: str) -> str:
        """Sucht Notizen nach Schlüsselwörtern"""
        # Extrahiere Suchbegriff
        search_term = self._extract_search_term(command)
        
        if not search_term:
            return "❌ Kein Suchbegriff gefunden. Beispiel: 'Suche Notizen nach Meeting'"
        
        # Suche in Notizen
        matching = [
            note for note in self.notes
            if search_term.lower() in note["content"].lower()
        ]
        
        if not matching:
            return f"ℹ️ Keine Notizen mit '{search_term}' gefunden."
        
        result = f"🔍 Gefundene Notizen für '{search_term}' ({len(matching)}):\n\n"
        
        for note in matching:
            date = datetime.fromisoformat(note["created_at"]).strftime("%d.%m.%Y %H:%M")
            result += f"#{note['id']} | {date}\n"
            result += f"   {note['content']}\n\n"
        
        return result.strip()
    
    def _delete_note(self, command: str) -> str:
        """Löscht Notiz(en)"""
        # Alle löschen?
        if "alle" in command:
            count = len(self.notes)
            self.notes.clear()
            self._save_notes()
            return f"🗑️ {count} Notizen gelöscht."
        
        # Einzelne Notiz löschen
        note_id = self._extract_number(command)
        
        if not note_id:
            return "❌ Keine Notiz-ID gefunden. Beispiel: 'Lösche Notiz 3'"
        
        # Finde und lösche Notiz
        for i, note in enumerate(self.notes):
            if note["id"] == note_id:
                deleted = self.notes.pop(i)
                self._save_notes()
                return f"🗑️ Notiz #{note_id} gelöscht: {deleted['content'][:50]}..."
        
        return f"❌ Notiz #{note_id} nicht gefunden."
    
    def _export_notes(self) -> str:
        """Exportiert alle Notizen als Text-Datei"""
        if not self.notes:
            return "ℹ️ Keine Notizen zum Exportieren."
        
        export_file = self.data_dir / f"notes_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        try:
            with open(export_file, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write("JARVIS NOTIZEN EXPORT\n")
                f.write(f"Datum: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")
                f.write("=" * 60 + "\n\n")
                
                for note in self.notes:
                    date = datetime.fromisoformat(note["created_at"]).strftime("%d.%m.%Y %H:%M")
                    f.write(f"Notiz #{note['id']} - {date}\n")
                    f.write("-" * 60 + "\n")
                    f.write(f"{note['content']}\n")
                    if note.get("tags"):
                        f.write(f"\nTags: {', '.join(note['tags'])}\n")
                    f.write("\n\n")
            
            return f"✅ {len(self.notes)} Notizen exportiert nach:\n{export_file}"
            
        except Exception as e:
            return f"❌ Fehler beim Exportieren: {str(e)}"
    
    def _extract_note_content(self, command: str) -> Optional[str]:
        """Extrahiert Notiz-Inhalt aus Befehl"""
        # Suche nach : Pattern
        if ":" in command:
            return command.split(":", 1)[1].strip()
        
        # Suche nach "notiz" Keyword
        keywords = ["notiere", "notiz", "neue notiz"]
        for kw in keywords:
            if kw in command.lower():
                idx = command.lower().find(kw) + len(kw)
                content = command[idx:].strip()
                # Entferne führende Sonderzeichen
                content = content.lstrip(":,.-")
                return content.strip()
        
        return None
    
    def _extract_tags(self, content: str) -> List[str]:
        """Extrahiert #tags aus Text"""
        import re
        return re.findall(r'#(\w+)', content)
    
    def _extract_number(self, text: str) -> Optional[int]:
        """Extrahiert erste Zahl aus Text"""
        import re
        match = re.search(r'\d+', text)
        return int(match.group()) if match else None
    
    def _extract_search_term(self, command: str) -> Optional[str]:
        """Extrahiert Suchbegriff"""
        keywords = ["nach", "für", "mit"]
        for kw in keywords:
            if kw in command:
                parts = command.split(kw, 1)
                if len(parts) > 1:
                    return parts[1].strip()
        return None


# Plugin Instance
_plugin_instance = None

def process(command: str, context: Dict[str, Any]) -> Optional[str]:
    """Entry point für JARVIS Plugin System"""
    global _plugin_instance
    if _plugin_instance is None:
        _plugin_instance = NotesPlugin()
    return _plugin_instance.process(command, context)
