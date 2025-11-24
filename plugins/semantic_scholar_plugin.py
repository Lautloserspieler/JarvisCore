"""Semantic Scholar Plugin fuer wissenschaftliche Artikel."""

from __future__ import annotations

import requests
from typing import Any, Dict, Optional

from utils.logger import Logger


class SemanticScholarPlugin:
    """Greift auf die Semantic-Scholar-API zu."""

    base_url = "https://api.semanticscholar.org/graph/v1/paper/search"

    def __init__(self, logger: Optional[Logger] = None) -> None:
        self.logger = logger or Logger()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "JARVIS-SemanticScholar-Plugin/1.0"
        })

    def search(self, query: str, limit: int = 3) -> Optional[str]:
        if not query:
            return None
        try:
            response = self.session.get(
                self.base_url,
                params={
                    "query": query,
                    "limit": limit,
                    "fields": "title,authors,venue,year,url",
                },
                timeout=10,
            )
            response.raise_for_status()
        except Exception as exc:
            self.logger.error(f"Fehler bei Semantic-Scholar-Suche: {exc}")
            return None

        data: Dict[str, Any] = response.json()
        papers = data.get("data") or []
        if not papers:
            return None

        lines = [f"Semantic Scholar Ergebnisse fuer '{query}':"]
        for paper in papers[:limit]:
            title = paper.get("title") or "Unbekannter Titel"
            authors = paper.get("authors") or []
            author_names = ", ".join(author.get("name", "?") for author in authors[:3])
            venue = paper.get("venue")
            year = paper.get("year")
            url = paper.get("url")
            entry = f"- {title} ({year or 'Jahr unbekannt'}) - {author_names}{' - ' + venue if venue else ''}{' - ' + url if url else ''}"
            lines.append(entry)
        return "\n".join(lines)

    def close(self) -> None:
        self.session.close()
