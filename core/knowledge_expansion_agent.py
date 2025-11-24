from __future__ import annotations

import random
import threading
import time
from typing import Any, Dict, List, Optional

from utils.logger import Logger


class KnowledgeExpansionAgent:
    """Hintergrundagent zum Auffinden neuer Wissensquellen."""

    def __init__(
        self,
        *,
        knowledge_manager: Any,
        learning_manager: Any,
        settings: Optional[Dict[str, Any]] = None,
        logger: Optional[Logger] = None,
    ) -> None:
        self.logger = logger or Logger()
        self.knowledge_manager = knowledge_manager
        self.learning_manager = learning_manager
        cfg = settings or {}
        self.enabled: bool = bool(cfg.get("enabled", True))
        self.interval_minutes: float = float(cfg.get("interval_minutes", 120.0))
        topics = cfg.get("topics") or [
            "kuenstliche intelligenz",
            "cybersecurity",
            "nachhaltigkeit",
            "forschung",
        ]
        self.topics: List[str] = [str(topic) for topic in topics if isinstance(topic, str) and topic.strip()]
        self.extra_sources: List[str] = []
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def start(self) -> None:
        if not self.enabled:
            self.logger.info("Knowledge Expansion Agent ist deaktiviert")
            return
        if self._thread and self._thread.is_alive():
            return
        self.logger.info("Knowledge Expansion Agent wird gestartet (%s Themen)", len(self.topics))
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="KnowledgeExpansionAgent", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._thread = None

    def add_topic(self, topic: str) -> None:
        normalized = topic.strip()
        if normalized and normalized not in self.topics:
            self.topics.append(normalized)

    def _run(self) -> None:
        cooldown = max(1.0, self.interval_minutes) * 60.0
        while not self._stop_event.is_set():
            topic = self._select_topic()
            if topic:
                self._harvest_topic(topic)
            self._stop_event.wait(cooldown)

    def _select_topic(self) -> Optional[str]:
        combined = self.topics + self.extra_sources
        if not combined:
            return None
        return random.choice(combined)

    def _harvest_topic(self, topic: str) -> None:
        try:
            self.logger.info("Knowledge Expansion: sammle neue Inhalte zu '%s'", topic)
            result = self.knowledge_manager.collect_knowledge_about_topic(topic)
            if result:
                self.learning_manager.mark_update("knowledge_expansion")
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.warning(f"Knowledge Expansion fehlgeschlagen fuer '{topic}': {exc}")


__all__ = ["KnowledgeExpansionAgent"]
