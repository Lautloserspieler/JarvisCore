"""PubMed plugin for biomedical article lookups."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import requests

from utils.logger import Logger


class PubMedPlugin:
    """Lightweight PubMed client using NCBI E-Utilities."""

    search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    summary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

    def __init__(self, logger: Optional[Logger] = None) -> None:
        self.logger = logger or Logger()
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "JARVIS-PubMed-Plugin/1.0 (+https://github.com/yourusername/jarvis)"}
        )

    def search(self, query: str, limit: int = 3) -> Optional[str]:
        if not query or not query.strip():
            return None
        try:
            ids = self._search_ids(query, limit=limit)
            if not ids:
                return f"Keine PubMed-Treffer zu '{query}' gefunden."
            summaries = self._fetch_summaries(ids)
            if not summaries:
                return f"Keine Details zu PubMed-Ergebnissen fuer '{query}' gefunden."
            lines = [f"PubMed-Treffer zu '{query}':"]
            for entry in summaries:
                title = entry.get("title") or "Ohne Titel"
                source = entry.get("source") or entry.get("fulljournalname") or ""
                year = self._extract_year(entry.get("pubdate"))
                lines.append(f"- {title} ({source}{', ' + year if year else ''})")
            return "\n".join(lines)
        except Exception as exc:
            self.logger.error(f"PubMed-Suche fehlgeschlagen: {exc}")
            return f"Bei der PubMed-Suche zu '{query}' ist ein Fehler aufgetreten."

    def _search_ids(self, query: str, *, limit: int = 3) -> List[str]:
        params = {
            "db": "pubmed",
            "retmode": "json",
            "retmax": max(1, min(limit, 10)),
            "term": query,
        }
        response = self.session.get(self.search_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        ids = data.get("esearchresult", {}).get("idlist", [])
        return [id_ for id_ in ids if isinstance(id_, str)]

    def _fetch_summaries(self, ids: List[str]) -> List[Dict[str, Any]]:
        params = {
            "db": "pubmed",
            "retmode": "json",
            "id": ",".join(ids),
        }
        response = self.session.get(self.summary_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        result = data.get("result", {})
        summaries: List[Dict[str, Any]] = []
        for uid in ids:
            entry = result.get(uid)
            if not entry:
                continue
            summaries.append(entry)
        return summaries

    @staticmethod
    def _extract_year(pubdate: Optional[str]) -> Optional[str]:
        if not pubdate or not isinstance(pubdate, str):
            return None
        parts = pubdate.strip().split()
        if not parts:
            return None
        year = parts[0]
        return year if year.isdigit() else None

    def close(self) -> None:
        try:
            self.session.close()
        except Exception:
            pass


__all__ = ["PubMedPlugin"]
