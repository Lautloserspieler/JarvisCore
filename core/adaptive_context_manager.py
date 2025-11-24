"""
Adaptive context management for J.A.R.V.I.S.

Extends the classic ContextManager with weighting of goal, mood and situation
signals. The manager keeps a light-weight context vector that can be used by
other subsystems (LLM routing, security, speech synthesis) to steer responses.
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional, Tuple

from .context_manager import ContextManager


@dataclass
class SignalState:
    """Holds the dynamic state of one adaptive signal."""

    name: str
    value: Optional[str] = None
    weight: float = 0.0
    confidence: float = 0.0
    last_update: float = field(default_factory=lambda: time.time())

    def decay(self, half_life: float) -> None:
        """Apply exponential decay to the confidence score."""
        now = time.time()
        elapsed = now - self.last_update
        if elapsed <= 0 or self.confidence <= 0:
            return
        if half_life <= 0:
            self.confidence = 0.0
            return
        decay_factor = 0.5 ** (elapsed / half_life)
        self.confidence *= decay_factor
        if self.confidence < 0.01:
            self.confidence = 0.0

    def update(self, value: Optional[str], confidence: float, weight: float) -> None:
        self.value = value
        self.confidence = max(0.0, min(1.0, confidence))
        self.weight = max(0.0, weight)
        self.last_update = time.time()


class AdaptiveContextManager(ContextManager):
    """
    Context manager that maintains weighted goal/mood/situation signals.

    The signals are automatically derived from user input but can also be
    updated explicitly through metadata.
    """

    DEFAULT_WEIGHTS = {"goal": 0.5, "mood": 0.3, "situation": 0.2}
    HALF_LIFE_SECONDS = 90.0

    ROUTE_RULES: Tuple[Tuple[str, str], ...] = (
        ("automation", "automation"),
        ("task", "task"),
        ("creative", "creative"),
        ("support", "empathetic"),
        ("default", "default"),
    )

    def __init__(
        self,
        *,
        enabled: bool = True,
        max_history: int = 20,
        weighting: Optional[Dict[str, float]] = None,
    ) -> None:
        super().__init__(enabled=enabled, max_history=max_history)
        weights = dict(self.DEFAULT_WEIGHTS)
        if weighting:
            for key, value in weighting.items():
                if key in weights:
                    weights[key] = max(0.0, float(value))
        total = sum(weights.values()) or 1.0
        self.weights = {key: value / total for key, value in weights.items()}
        self.signals: Dict[str, SignalState] = {
            name: SignalState(name=name, weight=self.weights[name]) for name in self.weights
        }

    # ------------------------------------------------------------------ #
    # public helpers
    # ------------------------------------------------------------------ #
    def observe(
        self,
        text: str,
        *,
        meta: Optional[Dict[str, Any]] = None,
        speaker: str = "user",
        intent: Optional[str] = None,
    ) -> None:
        """Analyse incoming text/meta and update adaptive signals."""
        if not self.enabled:
            return
        meta = meta or {}
        derived = self._derive_signals(text, meta, speaker=speaker, intent=intent)
        for name, (value, confidence) in derived.items():
            self._update_signal(name, value, confidence, meta)

    def select_logic_path(self, overrides: Optional[Dict[str, float]] = None) -> str:
        """
        Pick a logic route label based on the weighted signals.

        The selection is based on the strongest goal cluster with fallbacks.
        """
        scores = self.get_scores(apply_decay=True)
        if overrides:
            scores = {k: scores.get(k, 0.0) + float(v) for k, v in overrides.items()}
        goal_value = self.signals["goal"].value or "default"
        route = self._map_goal_to_route(goal_value)
        if route == "default":
            # fallback: pick the strongest weighted signal
            route = max(scores.items(), key=lambda item: item[1])[0] if scores else "default"
        return route

    def get_scores(self, *, apply_decay: bool = False) -> Dict[str, float]:
        """Return the weighted confidence scores for each signal."""
        result: Dict[str, float] = {}
        for name, state in self.signals.items():
            if apply_decay:
                state.decay(self.HALF_LIFE_SECONDS)
            result[name] = round(state.confidence * state.weight, 4)
        return result

    def snapshot(self) -> Dict[str, Any]:
        """Return a serialisable view of the adaptive context."""
        payload: Dict[str, Any] = {
            "scores": self.get_scores(apply_decay=False),
            "signals": {},
            "updated_at": datetime.fromtimestamp(time.time(), tz=timezone.utc).isoformat(),
        }
        for name, state in self.signals.items():
            payload["signals"][name] = {
                "value": state.value,
                "confidence": round(state.confidence, 3),
                "weight": round(state.weight, 3),
                "age": round(max(0.0, time.time() - state.last_update), 1),
            }
        payload["last_topic"] = self.get_topic()
        payload["entities"] = self.get_last_entities()
        return payload

    # ------------------------------------------------------------------ #
    # internal helpers
    # ------------------------------------------------------------------ #
    def _update_signal(self, name: str, value: Optional[str], confidence: float, meta: Dict[str, Any]) -> None:
        if name not in self.signals:
            return
        state = self.signals[name]
        weight_override = meta.get(f"{name}_weight")
        weight = state.weight if weight_override is None else max(0.0, float(weight_override))
        state.update(value, confidence, weight)

    def _derive_signals(
        self,
        text: str,
        meta: Dict[str, Any],
        *,
        speaker: str,
        intent: Optional[str],
    ) -> Dict[str, Tuple[Optional[str], float]]:
        """
        Heuristically derive signal values from user input, metadata and intent.

        Returns mapping: signal -> (value, confidence)
        """
        lower = (text or "").strip().lower()
        derived: Dict[str, Tuple[Optional[str], float]] = {}

        goal_value, goal_conf = self._infer_goal(lower, meta, intent)
        derived["goal"] = (goal_value, goal_conf)

        mood_value, mood_conf = self._infer_mood(lower, meta, speaker)
        derived["mood"] = (mood_value, mood_conf)

        situation_value, situation_conf = self._infer_situation(lower, meta, intent)
        derived["situation"] = (situation_value, situation_conf)

        return derived

    def _infer_goal(
        self,
        text: str,
        meta: Dict[str, Any],
        intent: Optional[str],
    ) -> Tuple[str, float]:
        explicit = meta.get("goal")
        if isinstance(explicit, str) and explicit:
            return explicit, 0.9

        if intent:
            if "task" in intent or "automation" in intent:
                return "automation", 0.75
            if "search" in intent or "knowledge" in intent:
                return "research", 0.65
            if "joke" in intent or "entertain" in intent:
                return "creative", 0.6

        task_keywords = ("erstelle", "baue", "generiere", "plane", "automatisiere", "skript", "workflow")
        research_keywords = ("erklaere", "was ist", "finde", "recherchiere", "warum")
        creative_keywords = ("geschichte", "gedicht", "song", "schreibe kreativ", "idee")
        support_keywords = ("hilfe", "unterstuetze", "problem", "ich brauche hilfe")

        if any(keyword in text for keyword in task_keywords):
            return "automation", 0.7
        if any(keyword in text for keyword in research_keywords):
            return "research", 0.6
        if any(keyword in text for keyword in creative_keywords):
            return "creative", 0.6
        if any(keyword in text for keyword in support_keywords):
            return "support", 0.55
        return "default", 0.25

    def _infer_mood(self, text: str, meta: Dict[str, Any], speaker: str) -> Tuple[str, float]:
        explicit = meta.get("mood")
        if isinstance(explicit, str) and explicit:
            return explicit, 0.9

        emotion = meta.get("emotion")
        if isinstance(emotion, str) and emotion:
            return emotion, 0.75

        negative_words = ("frustriert", "wütend", "genervt", "traurig", "hilfslos", "problem")
        positive_words = ("danke", "super", "toll", "freu", "glücklich", "entspannt")
        urgent_words = ("schnell", "dringend", "sofort")

        if any(word in text for word in negative_words):
            return "frustrated", 0.6
        if any(word in text for word in positive_words):
            return "positive", 0.55
        if speaker == "assistant" and any(word in text for word in urgent_words):
            return "alert", 0.5
        return "neutral", 0.3

    def _infer_situation(
        self,
        text: str,
        meta: Dict[str, Any],
        intent: Optional[str],
    ) -> Tuple[str, float]:
        explicit = meta.get("situation")
        if isinstance(explicit, str) and explicit:
            return explicit, 0.9

        if meta.get("environment") == "handsfree":
            return "handsfree", 0.6
        if meta.get("environment") == "noisy":
            return "noisy", 0.6
        if meta.get("channel") == "cli":
            return "desktop", 0.5

        urgent_words = ("sofort", "jetzt gleich", "dringend", "eilig")
        if any(word in text for word in urgent_words):
            return "urgent", 0.55

        if intent and "schedule" in intent:
            return "planning", 0.5
        if "remote" in text or "fern" in text:
            return "remote", 0.45
        return "standard", 0.3

    def _map_goal_to_route(self, goal: str) -> str:
        goal_lower = (goal or "default").lower()
        for match, route in self.ROUTE_RULES:
            if match in goal_lower:
                return route
        return "default"


__all__ = ["AdaptiveContextManager"]
