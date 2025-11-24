"""Wikidata plugin for structured lookups."""

from __future__ import annotations

from typing import Any, Dict, Optional

import requests

from utils.logger import Logger


class WikidataPlugin:
    """Fetch basic entity information from Wikidata."""

    search_url = "https://www.wikidata.org/w/api.php"
    entity_url = "https://www.wikidata.org/wiki/Special:EntityData/{entity_id}.json"

    def __init__(self, logger: Optional[Logger] = None) -> None:
        self.logger = logger or Logger()
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "JARVIS-Wikidata-Plugin/1.0"})

    def search(self, query: str, *, language: str = "de") -> Optional[str]:
        if not query or not query.strip():
            return None
        try:
            entity = self._search_entity(query.strip(), language=language)
            if not entity:
                return f"Keine Wikidata-Eintraege zu '{query}' gefunden."
            details = self._fetch_entity(entity["id"])
            if not details:
                return f"Wikidata-Eintrag {entity['id']} konnte nicht geladen werden."
            return self._format_entity(details, fallback_label=entity.get("label"))
        except Exception as exc:
            self.logger.error(f"Wikidata-Suche fehlgeschlagen: {exc}")
            return f"Bei der Wikidata-Suche zu '{query}' ist ein Fehler aufgetreten."

    def _search_entity(self, query: str, *, language: str = "de") -> Optional[Dict[str, Any]]:
        params = {
            "action": "wbsearchentities",
            "search": query,
            "language": language,
            "format": "json",
            "uselang": language,
            "limit": 3,
        }
        response = self.session.get(self.search_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        hits = data.get("search") or []
        if not hits:
            return None
        return hits[0]

    def _fetch_entity(self, entity_id: str) -> Optional[Dict[str, Any]]:
        response = self.session.get(self.entity_url.format(entity_id=entity_id), timeout=10)
        response.raise_for_status()
        data = response.json()
        entities = data.get("entities", {})
        return entities.get(entity_id)

    def _format_entity(self, entity: Dict[str, Any], *, fallback_label: Optional[str]) -> str:
        labels = entity.get("labels", {})
        descriptions = entity.get("descriptions", {})
        label = self._pick_locale(labels) or fallback_label or "Unbekannt"
        description = self._pick_locale(descriptions) or ""
        aliases = entity.get("aliases", {})
        alias_text = ", ".join(self._pick_aliases(aliases)[:5])

        lines = [f"Wikidata: {label} ({entity.get('id', '')})"]
        if description:
            lines.append(f"Beschreibung: {description}")
        if alias_text:
            lines.append(f"Aliase: {alias_text}")
        return "\n".join(lines)

    @staticmethod
    def _pick_locale(block: Dict[str, Dict[str, Any]]) -> Optional[str]:
        for lang in ("de", "en"):
            entry = block.get(lang)
            if entry and isinstance(entry.get("value"), str):
                return entry["value"]
        if block:
            first = next(iter(block.values()))
            if isinstance(first, dict):
                return first.get("value")
        return None

    @staticmethod
    def _pick_aliases(block: Dict[str, Any]) -> list[str]:
        aliases: list[str] = []
        for lang in ("de", "en"):
            entries = block.get(lang) or []
            for entry in entries:
                value = entry.get("value")
                if isinstance(value, str):
                    aliases.append(value)
        return aliases

    def close(self) -> None:
        try:
            self.session.close()
        except Exception:
            pass


__all__ = ["WikidataPlugin"]
