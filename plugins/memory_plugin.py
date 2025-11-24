"""Memory plugin that wraps the core memory manager."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from core.memory_manager import MemoryManager
from plugins.conversation_plugin_base import ConversationPlugin
from utils.logger import Logger


class MemoryPlugin(ConversationPlugin):
    """Stores conversation history and exposes short-term context."""

    plugin_name = "memory"

    def __init__(self, data_dir: str = "data", logger: Optional[Logger] = None) -> None:
        super().__init__(self.plugin_name)
        self.logger = logger or Logger()
        self.memory_manager = MemoryManager(data_dir=data_dir)
        self.session_dir = Path(data_dir) / "sessions"
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.session_file = self.session_dir / "session_active.json"
        self.session_start = datetime.now()
        self.session_id = "persistent_conversation"
        self.session_entries: List[Dict[str, Any]] = []
        self.previous_topics: List[str] = []
        self.previous_summary: str = ""
        self._load_existing_session()

    def on_user_message(self, message: str, context: Dict[str, Any]) -> None:
        timestamp = datetime.now()
        topics = context.get("detected_topics") if isinstance(context, dict) else None
        if not topics:
            fallback_topic = None
            if isinstance(context, dict):
                fallback_topic = context.get('last_topic') or context.get('last_command')
            if fallback_topic:
                topics = [str(fallback_topic)]
        self.memory_manager.add_to_conversation(
            role="user",
            content=message,
            timestamp=timestamp,
            topics=topics,
        )
        self._record_entry("user", message, context, topics=topics)

    def on_assistant_message(self, message: str, context: Dict[str, Any]) -> None:
        timestamp = datetime.now()
        self.memory_manager.add_to_conversation(
            role="assistant",
            content=message,
            timestamp=timestamp,
            topics=None,
        )
        self._record_entry("assistant", message, context)

    def get_context(self) -> Dict[str, Any]:
        summary = self.memory_manager.get_short_term_summary()
        context = {
            "active_topics": sorted(self.memory_manager.active_topics),
            "previous_topics": list(self.previous_topics),
        }
        if summary and not summary.strip().startswith("Kein aktueller Kontext"):
            context["memory_summary"] = summary
        if self.previous_summary:
            context.setdefault("memory_summary", self.previous_summary)
        return context

    def clear(self) -> None:
        self.memory_manager.clear_context()
        self.session_entries.clear()
        self._persist_session()

    def _load_existing_session(self) -> None:
        if not self.session_file.exists():
            return
        try:
            payload = json.loads(self.session_file.read_text(encoding="utf-8"))
        except Exception as exc:
            self.logger.debug(f"Sessions konnten nicht geladen werden: {exc}")
            return
        session_id = payload.get("session_id")
        if isinstance(session_id, str) and session_id.strip():
            self.session_id = session_id.strip()
        started_at = payload.get("started_at")
        if isinstance(started_at, str):
            try:
                self.session_start = datetime.fromisoformat(started_at)
            except ValueError:
                pass
        entries = payload.get("entries") or []
        if isinstance(entries, list):
            self.session_entries = [dict(entry) for entry in entries if isinstance(entry, dict)]
        else:
            self.session_entries = []
        for entry in self.session_entries:
            role = entry.get("role")
            content = entry.get("content")
            if not role or not content:
                continue
            timestamp = entry.get("timestamp")
            topics = entry.get("topics")
            dt_obj = None
            if isinstance(timestamp, str):
                try:
                    dt_obj = datetime.fromisoformat(timestamp)
                except ValueError:
                    dt_obj = None
            try:
                self.memory_manager.add_to_conversation(
                    role=role,
                    content=content,
                    timestamp=dt_obj,
                    topics=topics,
                )
            except Exception:
                continue
            if role == "user":
                self._update_previous_topics(topics)
        summary = payload.get("summary")
        if isinstance(summary, str):
            self.previous_summary = summary

    def _update_previous_topics(self, topics) -> None:
        if not topics:
            return
        if not isinstance(topics, (list, tuple)):
            topics = [topics]
        for topic in topics:
            if not topic:
                continue
            cleaned = str(topic).strip()
            if not cleaned:
                continue
            try:
                self.memory_manager.add_active_topic(cleaned)
            except Exception:
                pass
            if cleaned not in self.previous_topics:
                self.previous_topics.append(cleaned)

    def shutdown(self) -> None:  # pragma: no cover - convenience hook
        try:
            self._persist_session()
            self.memory_manager.clear_context()
        except Exception as exc:
            self.logger.debug(f"Memory plugin shutdown issue: {exc}")

    def _record_entry(
        self,
        role: str,
        content: str,
        context: Dict[str, Any],
        *,
        topics: Optional[Any] = None,
    ) -> None:
        if role == "user":
            if topics is None and isinstance(context, dict):
                topics = context.get("detected_topics")
            if not topics and isinstance(context, dict):
                fallback_topic = context.get("last_topic") or context.get("last_command")
                if fallback_topic:
                    topics = [str(fallback_topic)]
        if topics and not isinstance(topics, (list, tuple)):
            topics = [topics]
        entry = {
            "timestamp": datetime.now().isoformat(),
            "role": role,
            "content": content,
            "topics": list(topics) if topics else None,
        }
        if entry["topics"]:
            normalised_topics = [str(topic).strip() for topic in entry["topics"] if topic]
            entry["topics"] = [topic for topic in normalised_topics if topic]
            if not entry["topics"]:
                entry["topics"] = None
        if role == "user":
            self._update_previous_topics(entry.get('topics'))
        self.session_entries.append(entry)
        self._persist_session()

    def _persist_session(self) -> None:
        payload = {
            "session_id": self.session_id,
            "started_at": self.session_start.isoformat(),
            "updated_at": datetime.now().isoformat(),
            "entries": self.session_entries,
        }
        summary = self.memory_manager.get_short_term_summary()
        if summary and summary.strip():
            payload["summary"] = summary
        active_topics = sorted(self.memory_manager.active_topics)
        if active_topics:
            payload["active_topics"] = active_topics
        try:
            self.session_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as exc:
            self.logger.debug(f"Konnte Session-Datei nicht speichern: {exc}")
