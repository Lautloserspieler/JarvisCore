from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

DEFAULT_MEDIA_PREFS: Dict[str, Any] = {
    "preferred_target": None,
    "favorite_song": {
        "spotify": {"query": None, "uri": None},
        "youtube": {"query": None},
    },
    "favorite_playlist": {
        "spotify": {"name": None, "uri": None},
        "youtube": {"name": None},
    },
}


class MediaPreferences:
    """Simple JSON-backed storage for media preferences."""

    def __init__(self, data_dir: str = "data", filename: str = "user_media_prefs.json") -> None:
        self.path = Path(data_dir) / filename
        self._cache: Optional[Dict[str, Any]] = None

    def load(self) -> Dict[str, Any]:
        if self._cache is not None:
            return self._cache
        payload = DEFAULT_MEDIA_PREFS.copy()
        if self.path.exists():
            try:
                stored = json.loads(self.path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                stored = {}
            if isinstance(stored, dict):
                payload = self._merge_defaults(payload, stored)
        self._cache = payload
        return payload

    def save(self, payload: Dict[str, Any]) -> None:
        self._cache = payload
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def get_preferred_target(self) -> Optional[str]:
        prefs = self.load()
        target = prefs.get("preferred_target")
        if isinstance(target, str):
            lowered = target.lower().strip()
            if lowered in {"spotify", "youtube"}:
                return lowered
        return None

    def get_favorite_song(self, target: str) -> Dict[str, Optional[str]]:
        prefs = self.load()
        favorite = prefs.get("favorite_song")
        if not isinstance(favorite, dict):
            return {}
        target_block = favorite.get(target) if isinstance(target, str) else None
        if isinstance(target_block, dict):
            return {
                "query": self._clean_value(target_block.get("query")),
                "uri": self._clean_value(target_block.get("uri")),
            }
        return {}

    def get_favorite_playlist(self, target: str) -> Dict[str, Optional[str]]:
        prefs = self.load()
        favorite = prefs.get("favorite_playlist")
        if not isinstance(favorite, dict):
            return {}
        target_block = favorite.get(target) if isinstance(target, str) else None
        if isinstance(target_block, dict):
            return {
                "name": self._clean_value(target_block.get("name")),
                "uri": self._clean_value(target_block.get("uri")),
            }
        return {}

    def set_favorite_song(self, target: str, *, query: Optional[str] = None, uri: Optional[str] = None) -> None:
        prefs = self.load()
        favorite = prefs.setdefault("favorite_song", {})
        target_block = favorite.setdefault(target, {})
        if query is not None:
            target_block["query"] = query
        if uri is not None:
            target_block["uri"] = uri
        self.save(prefs)

    def set_favorite_playlist(self, target: str, *, name: Optional[str] = None, uri: Optional[str] = None) -> None:
        prefs = self.load()
        favorite = prefs.setdefault("favorite_playlist", {})
        target_block = favorite.setdefault(target, {})
        if name is not None:
            target_block["name"] = name
        if uri is not None:
            target_block["uri"] = uri
        self.save(prefs)

    def _merge_defaults(self, defaults: Dict[str, Any], stored: Dict[str, Any]) -> Dict[str, Any]:
        merged = dict(defaults)
        for key, value in stored.items():
            if key in defaults and isinstance(defaults[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_defaults(defaults[key], value)
            else:
                merged[key] = value
        return merged

    def _clean_value(self, value: Optional[str]) -> Optional[str]:
        if not isinstance(value, str):
            return None
        cleaned = value.strip()
        return cleaned or None


@dataclass
class MediaCommand:
    target: Optional[str]
    explicit_target: bool
    favorite_song: bool
    favorite_playlist: bool
    playlist_name: Optional[str]


_TARGET_ALIASES = {
    "spotify": ("spotify",),
    "youtube": ("youtube", "you tube", "yt"),
}


def parse_media_command(text: str, prefs: Optional[MediaPreferences] = None) -> MediaCommand:
    normalized = (text or "").lower()
    explicit_target = False
    target: Optional[str] = None
    for key, aliases in _TARGET_ALIASES.items():
        if any(re.search(rf"\b{re.escape(alias)}\b", normalized) for alias in aliases):
            target = key
            explicit_target = True
            break

    favorite_song = bool(re.search(r"\blieblings(?:song|lied)\b", normalized))
    favorite_playlist = "lieblingsplaylist" in normalized

    playlist_name = _extract_playlist_name(normalized)

    if not explicit_target and prefs is not None:
        preferred = prefs.get_preferred_target()
        if preferred:
            target = preferred

    return MediaCommand(
        target=target,
        explicit_target=explicit_target,
        favorite_song=favorite_song,
        favorite_playlist=favorite_playlist,
        playlist_name=playlist_name,
    )


def _extract_playlist_name(text: str) -> Optional[str]:
    if not text or "playlist" not in text or "lieblingsplaylist" in text:
        return None
    cleaned = _strip_target_phrases(text)
    match = re.search(r"\bplaylist\s+(?P<name>.+)", cleaned)
    if not match:
        return None
    name = match.group("name")
    name = re.sub(r"\b(ab|abspielen|starten|spielen)\b", " ", name)
    name = re.sub(r"[\s,.-]+", " ", name).strip()
    return name or None


def _strip_target_phrases(text: str) -> str:
    return re.sub(r"\s+(?:auf|bei|in)\s+(?:spotify|youtube|yt)\b.*$", "", text).strip()
