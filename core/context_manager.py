"""
Base Context Manager for J.A.R.V.I.S.

Provides fundamental context tracking functionality including:
- Conversation history management
- Entity tracking
- Topic detection
- Context window management
"""
from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Deque
import logging

logger = logging.getLogger(__name__)


@dataclass
class ContextEntry:
    """Single entry in conversation context."""
    timestamp: float = field(default_factory=time.time)
    speaker: str = "user"  # "user" or "assistant"
    text: str = ""
    intent: Optional[str] = None
    entities: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "timestamp": self.timestamp,
            "speaker": self.speaker,
            "text": self.text,
            "intent": self.intent,
            "entities": self.entities,
            "metadata": self.metadata,
        }


class ContextManager:
    """
    Base context manager for tracking conversation state.
    
    Maintains a rolling window of conversation history and extracts
    relevant context information for downstream processing.
    """

    def __init__(self, *, enabled: bool = True, max_history: int = 20):
        """
        Initialize ContextManager.
        
        Args:
            enabled: Whether context tracking is active
            max_history: Maximum number of context entries to retain
        """
        self.enabled = enabled
        self.max_history = max_history
        self.history: Deque[ContextEntry] = deque(maxlen=max_history)
        self._current_topic: Optional[str] = None
        self._entity_cache: Dict[str, Any] = {}
        logger.info(f"ContextManager initialized (enabled={enabled}, max_history={max_history})")

    def add_entry(
        self,
        text: str,
        *,
        speaker: str = "user",
        intent: Optional[str] = None,
        entities: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add a new entry to the context history.
        
        Args:
            text: The spoken/typed text
            speaker: Who said it ("user" or "assistant")
            intent: Detected intent if available
            entities: Named entities extracted from text
            metadata: Additional metadata
        """
        if not self.enabled:
            return

        entry = ContextEntry(
            text=text,
            speaker=speaker,
            intent=intent,
            entities=entities or {},
            metadata=metadata or {},
        )
        
        self.history.append(entry)
        
        # Update entity cache
        if entities:
            self._entity_cache.update(entities)
        
        # Update current topic if this is a user message
        if speaker == "user" and intent:
            self._current_topic = intent
        
        logger.debug(f"Added context entry: speaker={speaker}, intent={intent}")

    def get_history(self, limit: Optional[int] = None) -> List[ContextEntry]:
        """
        Get recent conversation history.
        
        Args:
            limit: Maximum number of entries to return (defaults to max_history)
            
        Returns:
            List of context entries, most recent last
        """
        if not self.enabled:
            return []
        
        entries = list(self.history)
        if limit is not None:
            entries = entries[-limit:]
        return entries

    def get_last_user_message(self) -> Optional[str]:
        """
        Get the most recent user message.
        
        Returns:
            Last user message text or None
        """
        for entry in reversed(self.history):
            if entry.speaker == "user":
                return entry.text
        return None

    def get_last_assistant_message(self) -> Optional[str]:
        """
        Get the most recent assistant message.
        
        Returns:
            Last assistant message text or None
        """
        for entry in reversed(self.history):
            if entry.speaker == "assistant":
                return entry.text
        return None

    def get_topic(self) -> Optional[str]:
        """
        Get the current conversation topic.
        
        Returns:
            Current topic/intent or None
        """
        return self._current_topic

    def get_last_entities(self) -> Dict[str, Any]:
        """
        Get entities from recent conversation.
        
        Returns:
            Dictionary of accumulated entities
        """
        return dict(self._entity_cache)

    def get_entity(self, key: str) -> Any:
        """
        Get a specific entity from the cache.
        
        Args:
            key: Entity key to retrieve
            
        Returns:
            Entity value or None if not found
        """
        return self._entity_cache.get(key)

    def clear(self) -> None:
        """Clear all context history and caches."""
        self.history.clear()
        self._entity_cache.clear()
        self._current_topic = None
        logger.info("Context cleared")

    def get_context_window(self, max_tokens: int = 2000) -> str:
        """
        Get formatted context window for LLM input.
        
        Args:
            max_tokens: Approximate maximum tokens (rough estimate)
            
        Returns:
            Formatted conversation history string
        """
        if not self.enabled or not self.history:
            return ""

        lines: List[str] = []
        total_chars = 0
        max_chars = max_tokens * 4  # Rough approximation

        # Build context from most recent backwards
        for entry in reversed(self.history):
            role = "User" if entry.speaker == "user" else "Assistant"
            line = f"{role}: {entry.text}"
            
            if total_chars + len(line) > max_chars:
                break
            
            lines.insert(0, line)
            total_chars += len(line)

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize context to dictionary.
        
        Returns:
            Dictionary representation of current context
        """
        return {
            "enabled": self.enabled,
            "max_history": self.max_history,
            "current_topic": self._current_topic,
            "entities": self._entity_cache,
            "history": [entry.to_dict() for entry in self.history],
        }

    def __len__(self) -> int:
        """Return number of entries in history."""
        return len(self.history)

    def __bool__(self) -> bool:
        """Return True if context has any history."""
        return len(self.history) > 0


__all__ = ["ContextManager", "ContextEntry"]
