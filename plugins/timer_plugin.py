"""Timer & Reminder Plugin for JARVIS"""

import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import re

# Plugin Metadata
PLUGIN_NAME = "Timer & Erinnerungen"
PLUGIN_DESCRIPTION = "Setzt Timer und Erinnerungen"
PLUGIN_VERSION = "1.0.0"
PLUGIN_AUTHOR = "Lautloserspieler"


class TimerPlugin:
    """Plugin für Timer und Erinnerungen"""
    
    def __init__(self):
        self.active_timers: List[Dict[str, Any]] = []
        self.active_reminders: List[Dict[str, Any]] = []
        self.timer_id_counter = 0
        
    def process(self, command: str, context: Dict[str, Any]) -> Optional[str]:
        """
        Verarbeitet Timer/Reminder-Anfragen
        
        Beispiele:
        - "Stelle Timer auf 5 Minuten"
        - "Timer 30 Sekunden"
        - "Erinnere mich in 2 Stunden"
        - "Erinnerung in 10 Minuten: Meeting"
        - "Zeige aktive Timer"
        - "Stoppe alle Timer"
        """
        command_lower = command.lower()
        
        # Timer starten
        if "timer" in command_lower and ("stelle" in command_lower or "starte" in command_lower or any(c.isdigit() for c in command)):
            return self._start_timer(command_lower)
        
        # Erinnerung setzen
        elif "erinner" in command_lower:
            return self._set_reminder(command_lower)
        
        # Status zeigen
        elif "zeige" in command_lower or "liste" in command_lower or "aktiv" in command_lower:
            return self._show_status()
        
        # Timer stoppen
        elif "stopp" in command_lower or "abbrech" in command_lower:
            return self._stop_timers()
        
        return None
    
    def _parse_duration(self, text: str) -> Optional[int]:
        """Parst Zeitangaben in Sekunden"""
        # Suche nach Zahlen + Einheiten
        patterns = [
            (r'(\d+)\s*stunde[n]?', 3600),
            (r'(\d+)\s*minute[n]?', 60),
            (r'(\d+)\s*sekunde[n]?', 1),
            (r'(\d+)\s*std', 3600),
            (r'(\d+)\s*min', 60),
            (r'(\d+)\s*sek', 1),
            (r'(\d+)\s*h', 3600),
            (r'(\d+)\s*m(?!i)', 60),  # m aber nicht mi (minute)
            (r'(\d+)\s*s(?!t)', 1),   # s aber nicht st (stunde)
        ]
        
        total_seconds = 0
        for pattern, multiplier in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                total_seconds += int(match) * multiplier
        
        return total_seconds if total_seconds > 0 else None
    
    def _start_timer(self, command: str) -> str:
        """Startet einen Timer"""
        duration = self._parse_duration(command)
        
        if not duration:
            return "❌ Keine gültige Zeitangabe gefunden. Beispiel: 'Timer 5 Minuten'"
        
        # Timer-ID generieren
        timer_id = self.timer_id_counter
        self.timer_id_counter += 1
        
        # Label extrahieren (falls vorhanden)
        label = self._extract_label(command)
        
        # Timer-Info speichern
        timer_info = {
            "id": timer_id,
            "duration": duration,
            "label": label,
            "start_time": datetime.now(),
            "end_time": datetime.now() + timedelta(seconds=duration)
        }
        self.active_timers.append(timer_info)
        
        # Timer im Hintergrund starten
        thread = threading.Thread(
            target=self._timer_thread,
            args=(timer_id, duration, label),
            daemon=True
        )
        thread.start()
        
        # Bestätigung
        duration_str = self._format_duration(duration)
        if label:
            return f"⏱️ Timer '{label}' gestartet: {duration_str}"
        else:
            return f"⏱️ Timer gestartet: {duration_str}"
    
    def _set_reminder(self, command: str) -> str:
        """Setzt eine Erinnerung"""
        duration = self._parse_duration(command)
        
        if not duration:
            return "❌ Keine gültige Zeitangabe gefunden. Beispiel: 'Erinnere mich in 30 Minuten'"
        
        # Nachricht extrahieren
        message = self._extract_reminder_message(command)
        if not message:
            message = "Erinnerung"
        
        # Erinnerungs-Info speichern
        reminder_info = {
            "message": message,
            "duration": duration,
            "start_time": datetime.now(),
            "trigger_time": datetime.now() + timedelta(seconds=duration)
        }
        self.active_reminders.append(reminder_info)
        
        # Erinnerung im Hintergrund starten
        thread = threading.Thread(
            target=self._reminder_thread,
            args=(duration, message),
            daemon=True
        )
        thread.start()
        
        duration_str = self._format_duration(duration)
        return f"🔔 Erinnerung gesetzt: '{message}' in {duration_str}"
    
    def _timer_thread(self, timer_id: int, duration: int, label: Optional[str]):
        """Timer-Thread der nach Ablauf benachrichtigt"""
        time.sleep(duration)
        
        # Timer aus Liste entfernen
        self.active_timers = [t for t in self.active_timers if t["id"] != timer_id]
        
        # TODO: Hier könnte TTS-Ausgabe oder Notification erfolgen
        label_str = f" '{label}'" if label else ""
        print(f"\n⏰ TIMER{label_str} ABGELAUFEN!\n")
    
    def _reminder_thread(self, duration: int, message: str):
        """Erinnerungs-Thread"""
        time.sleep(duration)
        
        # Erinnerung aus Liste entfernen
        self.active_reminders = [r for r in self.active_reminders if r["message"] != message]
        
        # TODO: TTS oder Notification
        print(f"\n🔔 ERINNERUNG: {message}\n")
    
    def _show_status(self) -> str:
        """Zeigt aktive Timer und Erinnerungen"""
        if not self.active_timers and not self.active_reminders:
            return "ℹ️ Keine aktiven Timer oder Erinnerungen."
        
        result = ""
        
        if self.active_timers:
            result += "⏱️ Aktive Timer:\n\n"
            for timer in self.active_timers:
                remaining = (timer["end_time"] - datetime.now()).total_seconds()
                if remaining > 0:
                    remaining_str = self._format_duration(int(remaining))
                    label = f" - {timer['label']}" if timer['label'] else ""
                    result += f"  • {remaining_str} verbleibend{label}\n"
            result += "\n"
        
        if self.active_reminders:
            result += "🔔 Aktive Erinnerungen:\n\n"
            for reminder in self.active_reminders:
                remaining = (reminder["trigger_time"] - datetime.now()).total_seconds()
                if remaining > 0:
                    remaining_str = self._format_duration(int(remaining))
                    result += f"  • '{reminder['message']}' in {remaining_str}\n"
        
        return result.strip()
    
    def _stop_timers(self) -> str:
        """Stoppt alle Timer"""
        count = len(self.active_timers) + len(self.active_reminders)
        
        if count == 0:
            return "ℹ️ Keine aktiven Timer zum Stoppen."
        
        self.active_timers.clear()
        self.active_reminders.clear()
        
        return f"✅ {count} Timer/Erinnerungen gestoppt."
    
    def _extract_label(self, command: str) -> Optional[str]:
        """Extrahiert Label aus Befehl"""
        # Suche nach : oder für Pattern
        patterns = [r':\s*(.+)', r'für\s+(.+)']
        for pattern in patterns:
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_reminder_message(self, command: str) -> Optional[str]:
        """Extrahiert Erinnerungsnachricht"""
        patterns = [r':\s*(.+)', r'an\s+(.+)', r'dass\s+(.+)']
        for pattern in patterns:
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _format_duration(self, seconds: int) -> str:
        """Formatiert Sekunden in lesbaren String"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        parts = []
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}min")
        if secs > 0 or not parts:
            parts.append(f"{secs}s")
        
        return " ".join(parts)


# Plugin Instance
_plugin_instance = None

def process(command: str, context: Dict[str, Any]) -> Optional[str]:
    """Entry point für JARVIS Plugin System"""
    global _plugin_instance
    if _plugin_instance is None:
        _plugin_instance = TimerPlugin()
    return _plugin_instance.process(command, context)
