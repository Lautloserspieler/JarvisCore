"""
Learning manager for Jarvis.

Collects reinforcement feedback, usage statistics and behavioural patterns
in order to adapt the assistant over time.
"""

from __future__ import annotations

import json
import threading
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from utils.logger import Logger


class LearningManager:
    """Persists reinforcement scores, usage counts and behaviour snapshots."""

    def __init__(self, storage_path: Optional[Path] = None) -> None:
        self.logger = Logger()
        self.storage_path = Path(storage_path or "data/learning_state.json")
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self.state: Dict[str, Any] = {
            "intent_stats": {},
            "intent_weights": {},
            "command_usage": {},
            "feedback_log": [],
            "time_histogram": {},
            "last_context": {},
            "last_update": {},
        }
        self._load()

    # ------------------------------------------------------------------ #
    # Persistence
    # ------------------------------------------------------------------ #
    def _load(self) -> None:
        try:
            if self.storage_path.exists():
                data = json.loads(self.storage_path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    self.state.update(data)
        except Exception as exc:
            self.logger.warning(f"Lernstatus konnte nicht geladen werden: {exc}")

    def _save(self) -> None:
        with self._lock:
            try:
                self.storage_path.write_text(json.dumps(self.state, ensure_ascii=False, indent=2), encoding="utf-8")
            except Exception as exc:
                self.logger.debug(f"Lernstatus konnte nicht gespeichert werden: {exc}")

    # ------------------------------------------------------------------ #
    # Recording helpers
    # ------------------------------------------------------------------ #
    def record_usage(self, intent: Optional[str], command_text: str) -> None:
        if not intent:
            return
        intent_stats = self.state.setdefault("intent_stats", {})
        stats = intent_stats.setdefault(intent, {"count": 0, "score": 0.0, "success": 0})
        stats["count"] += 1
        snippet = command_text.strip()
        if snippet:
            usage = self.state.setdefault("command_usage", {})
            usage[snippet] = usage.get(snippet, 0) + 1
        self._update_time_histogram(intent)
        self.state["last_context"]["last_intent"] = intent
        self.state["last_context"]["last_command"] = snippet
        self._save()

    def record_outcome(self, intent: Optional[str], success: bool) -> None:
        if not intent:
            return
        stats = self.state.setdefault("intent_stats", {}).setdefault(intent, {"count": 0, "score": 0.0, "success": 0})
        if success:
            stats["success"] = stats.get("success", 0) + 1
            stats["score"] = min(20.0, stats.get("score", 0.0) + 0.5)
        else:
            stats["score"] = max(-20.0, stats.get("score", 0.0) - 0.7)
        self._save()

    def record_feedback(
        self,
        score: float,
        message: str,
        *,
        correction: Optional[str] = None,
        intent: Optional[str] = None,
    ) -> Dict[str, Any]:
        timestamp = datetime.utcnow().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "score": score,
            "message": message,
        }
        if correction:
            log_entry["correction"] = correction
        if not intent:
            intent = self.state.get("last_context", {}).get("last_intent")
        if intent:
            log_entry["intent"] = intent
            stats = self.state.setdefault("intent_stats", {}).setdefault(
                intent, {"count": 0, "score": 0.0, "success": 0}
            )
            stats["score"] = max(-20.0, min(20.0, stats.get("score", 0.0) + score))
        self.state.setdefault("feedback_log", []).append(log_entry)
        self.state["last_context"]["pending_feedback"] = log_entry
        if intent:
            weight = self._apply_reinforcement(intent, score)
            log_entry["weight"] = weight
        self._save()
        return log_entry

    def _update_time_histogram(self, intent: str) -> None:
        try:
            hour = datetime.now().hour
        except Exception:
            hour = int(time.time() // 3600 % 24)
        hist = self.state.setdefault("time_histogram", {})
        bucket = hist.setdefault(str(hour), {"total": 0, "intents": {}})
        bucket["total"] += 1
        bucket["intents"][intent] = bucket["intents"].get(intent, 0) + 1

    # ------------------------------------------------------------------ #
    # Derived metrics
    # ------------------------------------------------------------------ #
    def get_intent_bias(self, intent: str) -> float:
        stats = self.state.get("intent_stats", {}).get(intent)
        if not stats:
            return 0.0
        score = float(stats.get("score", 0.0))
        # Map [-20,20] roughly to [-0.2, 0.2]
        return max(-0.2, min(0.2, score / 100.0))

    def get_top_commands(self, limit: int = 5) -> List[Tuple[str, int]]:
        usage = self.state.get("command_usage", {})
        return sorted(usage.items(), key=lambda item: item[1], reverse=True)[:limit]

    def get_behavior_summary(self) -> Dict[str, Any]:
        histogram = self.state.get("time_histogram", {})
        if not histogram:
            return {}
        totals = {int(hour): data.get("total", 0) for hour, data in histogram.items()}
        if not totals:
            return {}
        peak = max(totals, key=totals.get)
        quiet = min(totals, key=totals.get)
        preferred_intents: Dict[str, int] = defaultdict(int)
        for data in histogram.values():
            for intent, count in data.get("intents", {}).items():
                preferred_intents[intent] += count
        top_intents = sorted(preferred_intents.items(), key=lambda item: item[1], reverse=True)[:3]
        return {
            "peak_hour": peak,
            "quiet_hour": quiet,
            "top_intents": top_intents,
        }

    def mark_update(self, category: str) -> None:
        self.state.setdefault("last_update", {})[category] = datetime.utcnow().isoformat()
        self._save()

    def get_snapshot(self) -> Dict[str, Any]:
        top_commands = [
            {"command": command, "count": count}
            for command, count in self.get_top_commands()
        ]
        snapshot: Dict[str, Any] = {
            "top_commands": top_commands,
            "behavior": self.get_behavior_summary(),
            "last_update": self.state.get("last_update", {}),
        }
        pending = self.state.get("last_context", {}).get("pending_feedback")
        if pending:
            snapshot["pending_feedback"] = pending
        return snapshot

    def consume_pending_feedback(self) -> Optional[Dict[str, Any]]:
        pending = self.state.get("last_context", {}).pop("pending_feedback", None)
        if pending:
            self._save()
        return pending

    def run_retraining(self) -> Dict[str, Any]:
        """Placeholder retraining step based auf Feedback-Log."""
        feedback_entries = self.state.get("feedback_log", []) or []
        summary = {
            "feedback_entries": len(feedback_entries),
            "last_feedback": feedback_entries[-1] if feedback_entries else None,
        }
        self.state.setdefault("last_update", {})["retraining"] = datetime.utcnow().isoformat()
        self._save()
        return summary

    # ------------------------------------------------------------------ #
    # Reinforcement learning helpers
    # ------------------------------------------------------------------ #
    def _apply_reinforcement(self, intent: str, score: float) -> float:
        weights = self.state.setdefault("intent_weights", {})
        current = float(weights.get(intent, 0.0))
        adjusted = max(-1.0, min(1.0, current + score * 0.05))
        weights[intent] = adjusted
        self.state.setdefault("last_update", {})["reinforcement"] = datetime.utcnow().isoformat()
        return adjusted

    def get_reinforcement_weight(self, intent: str) -> float:
        return float(self.state.get("intent_weights", {}).get(intent, 0.0))

    def get_reinforcement_snapshot(self) -> Dict[str, float]:
        weights = self.state.get("intent_weights", {})
        return {intent: float(weight) for intent, weight in weights.items()}

