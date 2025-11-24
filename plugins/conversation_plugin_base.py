"""Gemeinsame Basisklasse für Konversations-Plugins.

Die bisherigen Plugins (z. B. memory_plugin, clarification_plugin) erwarten
eine leichte Basisklasse, die grundlegende Attribute bereitstellt. Die Datei
war offenbar nicht mehr im Projekt vorhanden, daher liefern wir eine kleine
Ersatz-Implementierung.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


class ConversationPlugin:
    """Minimaler Grundstock für Konversations-Plugins."""

    plugin_name: str = "conversation-plugin"

    def __init__(self, name: Optional[str] = None) -> None:
        if name:
            self.plugin_name = name

    # Sämtliche Methoden sind optional und können von den abgeleiteten
    # Plugins überschrieben werden. Die Basisklasse liefert jeweils nur
    # eine neutrale Default-Implementierung.

    def on_user_message(self, message: str, context: Dict[str, Any]) -> Optional[str]:
        return None

    def on_assistant_message(self, message: str, context: Dict[str, Any]) -> None:
        return None

    def get_context(self) -> Dict[str, Any]:
        return {}

    def shutdown(self) -> None:
        return None
