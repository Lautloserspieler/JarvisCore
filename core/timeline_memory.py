"""
Timeline memory keeps chronological events for Jarvis.

Events are stored in JSON and can be queried by type, time range or fuzzy text.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


def _timestamp(value: Optional[str]) -> str:
    if value:
        return value
    return datetime.utcnow().isoformat()


@dataclass
class TimelineEvent:
    event_type: str
    payload: Dict[str, Any]
    timestamp: str
    importance: float = 0.5

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "importance": round(float(self.importance), 4),
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "TimelineEvent":
        return TimelineEvent(
            event_type=data.get("event_type", "generic"),
            payload=dict(data.get("payload") or {}),
            timestamp=_timestamp(data.get("timestamp")),
            importance=float(data.get("importance", 0.5)),
        )


class TimelineMemory:
    """Persisted chronological memory."""

    def __init__(self, storage_file: str, *, max_events: int = 4096) -> None:
        self.storage_path = Path(storage_file)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.max_events = max_events
        self.events: List[TimelineEvent] = []
        self._load()

    # ------------------------------------------------------------------ #
    # persistence
    # ------------------------------------------------------------------ #
    def _load(self) -> None:
        if not self.storage_path.exists():
            return
        try:
            payload = json.loads(self.storage_path.read_text(encoding="utf-8"))
            self.events = [TimelineEvent.from_dict(item) for item in payload]
            self.events.sort(key=lambda item: item.timestamp)
        except Exception:
            self.events = []

    def _save(self) -> None:
        snapshot = [event.to_dict() for event in self.events[-self.max_events :]]
        self.storage_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")

    # ------------------------------------------------------------------ #
    # public api
    # ------------------------------------------------------------------ #
    def add_event(
        self,
        event_type: str,
        payload: Optional[Dict[str, Any]] = None,
        *,
        timestamp: Optional[str] = None,
        importance: float = 0.5,
    ) -> None:
        event = TimelineEvent(
            event_type=event_type,
            payload=payload or {},
            timestamp=_timestamp(timestamp),
            importance=max(0.0, min(1.0, importance)),
        )
        self.events.append(event)
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events :]
        self.events.sort(key=lambda item: item.timestamp)
        self._save()

    def query(
        self,
        *,
        event_type: Optional[str] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
        limit: int = 50,
        search_text: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        start_dt = datetime.fromisoformat(start) if start else None
        end_dt = datetime.fromisoformat(end) if end else None
        search_lower = (search_text or "").lower()
        filtered: List[TimelineEvent] = []
        for event in reversed(self.events):
            if event_type and event.event_type != event_type:
                continue
            event_dt = datetime.fromisoformat(event.timestamp)
            if start_dt and event_dt < start_dt:
                continue
            if end_dt and event_dt > end_dt:
                continue
            if search_lower:
                payload_text = json.dumps(event.payload, ensure_ascii=False).lower()
                if search_lower not in payload_text:
                    continue
            filtered.append(event)
            if len(filtered) >= limit:
                break
        filtered.reverse()
        return [event.to_dict() for event in filtered]

    def clear(self) -> None:
        self.events = []
        self._save()
