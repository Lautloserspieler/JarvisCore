"""
Light-weight vector memory for semantic lookup without external dependencies.

Implements a simple bag-of-words embedding with cosine similarity scoring.
"""
from __future__ import annotations

import json
import math
import re
import uuid
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


TOKEN_PATTERN = re.compile(r"\b[\wÄÖÜäöüß]+\b", re.UNICODE)


def _normalize(value: float) -> float:
    return round(float(value), 6)


@dataclass
class VectorEntry:
    entry_id: str
    text: str
    embedding: Dict[str, float]
    metadata: Dict[str, str]
    timestamp: str
    importance: float = 0.5

    def to_payload(self) -> Dict[str, Any]:
        return {
            "id": self.entry_id,
            "text": self.text,
            "embedding": {token: _normalize(weight) for token, weight in self.embedding.items()},
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "importance": _normalize(self.importance),
        }

    @staticmethod
    def from_payload(payload: Dict[str, Any]) -> "VectorEntry":
        return VectorEntry(
            entry_id=payload["id"],
            text=payload["text"],
            embedding={k: float(v) for k, v in payload.get("embedding", {}).items()},
            metadata=dict(payload.get("metadata") or {}),
            timestamp=payload.get("timestamp") or datetime.utcnow().isoformat(),
            importance=float(payload.get("importance", 0.5)),
        )


class VectorMemory:
    """Maintains a set of vectorised memories for semantic lookup."""

    def __init__(self, storage_file: str, *, max_entries: int = 2048) -> None:
        self.storage_path = Path(storage_file)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.max_entries = max_entries
        self.entries: List[VectorEntry] = []
        self._load()

    # ------------------------------------------------------------------ #
    # persistence
    # ------------------------------------------------------------------ #
    def _load(self) -> None:
        if not self.storage_path.exists():
            return
        try:
            data = json.loads(self.storage_path.read_text(encoding="utf-8"))
            self.entries = [VectorEntry.from_payload(item) for item in data]
        except Exception:
            self.entries = []

    def _save(self) -> None:
        payload = [entry.to_payload() for entry in self.entries[-self.max_entries :]]
        self.storage_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    # ------------------------------------------------------------------ #
    # vector operations
    # ------------------------------------------------------------------ #
    def _tokenize(self, text: str) -> Iterable[str]:
        if not text:
            return []
        return [token.lower() for token in TOKEN_PATTERN.findall(text)]

    def _vectorize(self, text: str) -> Dict[str, float]:
        tokens = list(self._tokenize(text))
        if not tokens:
            return {}
        counts = Counter(tokens)
        norm = math.sqrt(sum(value * value for value in counts.values())) or 1.0
        return {token: count / norm for token, count in counts.items() if count}

    @staticmethod
    def _cosine(vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
        if not vec_a or not vec_b:
            return 0.0
        # Ensure iterates on shortest vector
        if len(vec_a) > len(vec_b):
            vec_a, vec_b = vec_b, vec_a
        score = sum(weight * vec_b.get(token, 0.0) for token, weight in vec_a.items())
        if not score:
            return 0.0
        denom_a = math.sqrt(sum(weight * weight for weight in vec_a.values()))
        denom_b = math.sqrt(sum(weight * weight for weight in vec_b.values()))
        denom = denom_a * denom_b or 1.0
        return score / denom

    # ------------------------------------------------------------------ #
    # public api
    # ------------------------------------------------------------------ #
    def add_entry(
        self,
        text: str,
        *,
        metadata: Optional[Dict[str, Any]] = None,
        importance: float = 0.5,
        embedding: Optional[Dict[str, float]] = None,
    ) -> str:
        metadata = {k: str(v) for k, v in (metadata or {}).items()}
        vector = embedding or self._vectorize(text)
        entry_id = str(uuid.uuid4())
        entry = VectorEntry(
            entry_id=entry_id,
            text=text,
            embedding=vector,
            metadata=metadata,
            timestamp=datetime.utcnow().isoformat(),
            importance=max(0.0, min(1.0, importance)),
        )
        self.entries.append(entry)
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[-self.max_entries :]
        self._save()
        return entry_id

    def search(self, query: str, *, top_k: int = 5, min_score: float = 0.25) -> List[Dict[str, Any]]:
        vector = self._vectorize(query)
        results: List[Tuple[float, VectorEntry]] = []
        for entry in self.entries:
            score = self._cosine(vector, entry.embedding)
            if score >= min_score:
                results.append((score, entry))
        results.sort(key=lambda item: item[0], reverse=True)
        limited = results[: max(1, top_k)]
        return [
            {
                "id": entry.entry_id,
                "text": entry.text,
                "metadata": entry.metadata,
                "timestamp": entry.timestamp,
                "importance": entry.importance,
                "score": round(score, 4),
            }
            for score, entry in limited
        ]

    def clear(self) -> None:
        self.entries = []
        self._save()
