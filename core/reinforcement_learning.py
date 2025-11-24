"""
Reinforcement Learning Kern fuer J.A.R.V.I.S.

Verarbeitet Feedback in Echtzeit, aktualisiert Lerngewichte und stellt
Kurzzeitsignale fuer andere Komponenten bereit.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Deque, Dict, Optional

from utils.logger import Logger


class ReinforcementLearningCore:
    """Erfasst Nutzerfeedback und stellt sofortige Anpassungssignale bereit."""

    def __init__(self, learning_manager: Any, *, logger: Optional[Logger] = None, window_size: int = 20) -> None:
        self.logger = logger or Logger()
        self.learning_manager = learning_manager
        self.recent_feedback: Deque[Dict[str, Any]] = deque(maxlen=max(5, window_size))
        self.latest_weights: Dict[str, float] = {}

    def register_feedback(self, entry: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not entry:
            return None
        intent = entry.get("intent")
        weight = None
        if intent:
            weight = self.learning_manager.get_reinforcement_weight(intent)
            self.latest_weights[intent] = weight
        payload = {
            "intent": intent,
            "score": entry.get("score"),
            "weight": weight,
            "message": entry.get("message"),
            "timestamp": entry.get("timestamp"),
        }
        if entry.get("correction"):
            payload["correction"] = entry["correction"]
        self.recent_feedback.append(payload)
        self.logger.debug(
            "Reinforcement update intent=%s score=%s weight=%s",
            intent,
            entry.get("score"),
            weight,
        )
        return payload

    def get_recent_feedback(self) -> Dict[str, Any]:
        return {
            "recent": list(self.recent_feedback),
            "weights": dict(self.latest_weights),
        }


__all__ = ["ReinforcementLearningCore"]
