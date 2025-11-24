from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from utils.logger import Logger
from utils.text_shortener import condense_text


class LongTermTrainer:
    """Analysiert vergangene Dialoge und aktualisiert Verhaltensmuster."""

    def __init__(
        self,
        *,
        memory_manager: Optional[Any] = None,
        learning_manager: Any,
        knowledge_manager: Any,
        logger: Optional[Logger] = None,
    ) -> None:
        self.logger = logger or Logger()
        self.memory_manager = memory_manager
        self.learning_manager = learning_manager
        self.knowledge_manager = knowledge_manager
        self.last_summary: Optional[Dict[str, Any]] = None
        self.command_processor: Optional[Any] = None

    def run_cycle(self) -> Optional[Dict[str, Any]]:
        try:
            conversation_summary = self._summarise_conversations()
            knowledge_summary = self._summarise_knowledge_updates()
            payload = {
                "timestamp": datetime.utcnow().isoformat(),
                "conversation": conversation_summary,
                "knowledge": knowledge_summary,
            }
            if self.memory_manager:
                self.memory_manager.remember(
                    key=f"long_term_training_{payload['timestamp']}",
                    value=payload,
                    category="long_term_training",
                    importance=7,
                    source="trainer",
                )
            else:
                try:
                    self.knowledge_manager.cache_knowledge(
                        topic=f"long_term_training_{payload['timestamp']}",
                        content=str(payload),
                        source="LongTermTrainer",
                    )
                except Exception:
                    pass
            self.learning_manager.mark_update("long_term_trainer")
            self.last_summary = payload
            return payload
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.warning(f"Long-Term Trainer konnte nicht ausgefuehrt werden: {exc}")
            return None

    def set_command_processor(self, processor: Any) -> None:
        self.command_processor = processor

    def _summarise_conversations(self) -> str:
        texts: List[str] = []
        if self.memory_manager and hasattr(self.memory_manager, "query_timeline"):
            timeline = self.memory_manager.query_timeline(event_type="conversation", limit=40)
            for entry in timeline or []:
                payload = entry.get("payload") or {}
                if isinstance(payload, dict):
                    role = payload.get("role", "user")
                    content = payload.get("content")
                    if content:
                        texts.append(f"[{role}] {content}")
        elif self.command_processor:
            history = self.command_processor.context.get('conversation_history', [])
            for item in history[-40:]:
                if isinstance(item, dict):
                    if 'user' in item:
                        role = 'user'
                        content = item.get('user')
                    elif 'assistant' in item:
                        role = 'assistant'
                        content = item.get('assistant')
                    else:
                        continue
                    if content:
                        texts.append(f"[{role}] {content}")
        if not texts:
            return "Keine neuen Konversationen zur Analyse."
        joined = " \n".join(texts)
        return condense_text(joined, min_length=160, max_length=600)

    def _summarise_knowledge_updates(self) -> str:
        try:
            stats = self.knowledge_manager.get_knowledge_stats()
        except Exception:
            stats = {}
        baseline = [f"Wissensdatenbank: {stats.get('articles', 0)} Artikel"]
        baseline.append(f"Cache-Eintrage: {stats.get('cached_searches', 0)}")
        baseline.append(f"Feedback: {stats.get('feedback_entries', 0)}")
        return "; ".join(baseline)


__all__ = ["LongTermTrainer"]
