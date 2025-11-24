"""Benutzerpräferenzen- und Gewohnheitsmanager.

- Persistiert einfache Nutzungsstatistiken und Präferenzen in `data/preferences.json`
- Bietet APIs zum Erhöhen von Zählern und Abrufen bevorzugter Optionen
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional, Any, List, Tuple

from utils.logger import Logger


class PreferencesManager:
    def __init__(self, path: Optional[Path] = None) -> None:
        self.logger = Logger()
        self.path = Path(path) if path else Path("data/preferences.json")
        self.data: Dict[str, Any] = {
            "usage": {},  # e.g. {"intent:greeting": 12}
            "defaults": {},  # arbitrary key->value preferences
        }
        self._load()

    # ------------------------- Persistence -------------------------
    def _load(self) -> None:
        try:
            if self.path.exists():
                self.data = json.loads(self.path.read_text(encoding="utf-8"))
            else:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                self._save()
        except Exception as exc:
            self.logger.warning(f"Preferences konnten nicht geladen werden: {exc}")

    def _save(self) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as exc:
            self.logger.error(f"Preferences konnten nicht gespeichert werden: {exc}")

    # ------------------------- Usage tracking -------------------------
    def inc_usage(self, key: str, amount: int = 1) -> None:
        if not key:
            return
        usage = self.data.setdefault("usage", {})
        usage[key] = int(usage.get(key, 0)) + int(amount)
        self._save()

    def top_usage(self, prefix: str, *, limit: int = 5) -> List[Tuple[str, int]]:
        usage = self.data.get("usage", {})
        filtered = [(k, int(v)) for k, v in usage.items() if k.startswith(prefix)]
        filtered.sort(key=lambda kv: kv[1], reverse=True)
        return filtered[:limit]

    # ------------------------- Defaults -------------------------
    def set_default(self, key: str, value: Any) -> None:
        self.data.setdefault("defaults", {})[key] = value
        self._save()

    def get_default(self, key: str, default: Any = None) -> Any:
        return self.data.get("defaults", {}).get(key, default)


__all__ = ["PreferencesManager"]
