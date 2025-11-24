"""Open Library Plugin fuer Buchinformationen."""

from __future__ import annotations

import requests
from typing import Any, Dict, List, Optional

from utils.logger import Logger


class OpenLibraryPlugin:
    """Einfaches Wrapper-Plugin fuer die Open-Library-Suche."""

    base_url = "https://openlibrary.org/search.json"

    def __init__(self, logger: Optional[Logger] = None) -> None:
        self.logger = logger or Logger()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "JARVIS-OpenLibrary-Plugin/1.0"
        })

    def search(self, query: str, limit: int = 3) -> Optional[str]:
        if not query:
            return None
        try:
            response = self.session.get(
                self.base_url,
                params={"q": query, "limit": limit},
                timeout=10,
            )
            response.raise_for_status()
        except Exception as exc:
            self.logger.error(f"Fehler bei OpenLibrary-Suche: {exc}")
            return None

        data = response.json()
        docs: List[Dict[str, Any]] = data.get("docs", [])
        if not docs:
            return None

        lines = [f"OpenLibrary Ergebnisse fuer '{query}':"]
        for doc in docs[:limit]:
            title = doc.get("title") or "Unbekannter Titel"
            author = ", ".join(doc.get("author_name", [])[:2]) or "Unbekannter Autor"
            year = doc.get("first_publish_year")
            entry = f"- {title} ({author}{', ' + str(year) if year else ''})"
            lines.append(entry)
        return "\n".join(lines)

    def close(self) -> None:
        self.session.close()
