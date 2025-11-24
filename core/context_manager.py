"""Konversationskontext-Manager

Hält kurzzeitigen Kontext wie letztes Thema und erkannte Entitäten.
Bietet einfache Pronomen-Auflösung ("das", "es") und Turn-Tracking.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Turn:
    role: str  # 'user' | 'assistant'
    text: str
    meta: Dict[str, Any] = field(default_factory=dict)


class ContextManager:
    def __init__(self, *, enabled: bool = True, max_history: int = 20) -> None:
        self.enabled = enabled
        self.max_history = max_history
        self.turns: List[Turn] = []
        self.last_topic: str = ""
        self.last_entities: Dict[str, str] = {}
        # einfache Pronomen-Liste (de) — 'es' entfernt, um Fragen wie "wie spaet ist es" nicht zu verfremden
        self._pronouns = re.compile(r"\b(das|dies|dieses|den|dem|die)\b", flags=re.IGNORECASE)

    # ---------------------- turns ----------------------
    def _trim(self) -> None:
        if len(self.turns) > self.max_history:
            self.turns = self.turns[-self.max_history :]

    def update_on_user(self, text: str, meta: Optional[Dict[str, Any]] = None) -> None:
        if not self.enabled:
            return
        self.turns.append(Turn("user", text or "", meta or {}))
        self._trim()

    def update_on_assistant(self, text: str, meta: Optional[Dict[str, Any]] = None) -> None:
        if not self.enabled:
            return
        self.turns.append(Turn("assistant", text or "", meta or {}))
        self._trim()

    # ---------------------- intents/entities ----------------------
    def update_from_intent(self, intent_name: str, entities: Optional[Dict[str, str]] = None, *, text: str = "") -> None:
        if not self.enabled:
            return
        ents = entities or {}
        # sehr einfache Heuristik: Thema = wichtigstes Entity oder der Text
        topic = ents.get("topic") or ents.get("program") or ents.get("program_den") or text
        if topic:
            self.last_topic = topic.strip()
        if ents:
            self.last_entities = {k: v for k, v in ents.items() if isinstance(v, str) and v.strip()}

    # ---------------------- retrieval ----------------------
    def get_topic(self) -> str:
        return self.last_topic

    def get_last_entities(self) -> Dict[str, str]:
        return dict(self.last_entities)

    # ---------------------- resolution ----------------------
    def resolve_pronouns(self, text: str) -> str:
        """Ersetzt einfache Pronomen mit dem zuletzt bekannten Thema (falls vorhanden)."""
        if not self.enabled or not text:
            return text
        topic = (self.last_topic or "").strip()
        if not topic:
            return text
        return self._pronouns.sub(topic, text)


__all__ = ["ContextManager"]
