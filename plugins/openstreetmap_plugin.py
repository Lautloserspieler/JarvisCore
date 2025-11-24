"""OpenStreetMap Plugin fuer Ortsabfragen."""

from __future__ import annotations

import requests
from typing import Any, Dict, List, Optional

from utils.logger import Logger


class OpenStreetMapPlugin:
    """Verwendet den Nominatim-Dienst fuer einfache Ortsbeschreibungen."""

    base_url = "https://nominatim.openstreetmap.org/search"

    def __init__(self, logger: Optional[Logger] = None) -> None:
        self.logger = logger or Logger()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "JARVIS-OSM-Plugin/1.0"
        })

    def search(self, query: str, limit: int = 3) -> Optional[str]:
        if not query:
            return None
        try:
            response = self.session.get(
                self.base_url,
                params={
                    "q": query,
                    "format": "json",
                    "limit": limit,
                    "addressdetails": 1,
                },
                timeout=10,
            )
            response.raise_for_status()
        except Exception as exc:
            self.logger.error(f"Fehler bei OpenStreetMap-Suche: {exc}")
            return None

        results: List[Dict[str, Any]] = response.json()
        if not results:
            return None

        lines = [f"OpenStreetMap Hinweise fuer '{query}':"]
        for item in results[:limit]:
            display = item.get("display_name") or "Unbekannter Ort"
            lat = item.get("lat")
            lon = item.get("lon")
            entry = f"- {display} (Lat: {lat}, Lon: {lon})"
            lines.append(entry)
        return "\n".join(lines)

    def close(self) -> None:
        self.session.close()
