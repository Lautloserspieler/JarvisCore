"""Wikipedia plugin providing German Wikipedia lookups for J.A.R.V.I.S."""

import time
from typing import Dict, List, Optional
from urllib.parse import quote

import requests

from utils.logger import Logger
from utils.text_shortener import condense_text


class WikipediaPlugin:
    """Small helper around the German Wikipedia API."""

    def __init__(self) -> None:
        self.logger = Logger()
        self.base_url = "https://de.wikipedia.org/api/rest_v1"
        self.api_url = "https://de.wikipedia.org/w/api.php"
        self.timeout = 10
        self.max_retries = 3
        self.retry_backoff = 0.8

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "J.A.R.V.I.S./1.0 (Deutschsprachiger Sprachassistent)"
        })

        self.logger.info("Wikipedia plugin initialised")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def search(self, query: str, limit: int = 5) -> Optional[str]:
        """Return a nicely formatted article summary for the given query."""
        if not query or not query.strip():
            return None

        raw_query = query.strip()
        cleaned_query = self._normalize_query(raw_query)
        lookup_term = cleaned_query or raw_query

        self.logger.info("Wikipedia search: %s", lookup_term)

        try:
            resolved_title = self._resolve_title(lookup_term)
            if resolved_title:
                summary = self._get_article_summary(resolved_title)
                if summary:
                    return summary

            search_results = self._search_articles(lookup_term, max_results=limit)
            if not search_results:
                return f"Keine Wikipedia-Artikel zu '{lookup_term}' gefunden."

            best_match = self._pick_best_match(lookup_term, search_results)
            article_summary = self._get_article_summary(best_match)
            if article_summary:
                suggestions = [title for title in search_results if title != best_match]
                return self._format_result(best_match, article_summary, suggestions)

            return f"Keine detaillierten Informationen zu '{lookup_term}' gefunden."
        except Exception as exc:  # pragma: no cover - logged for debugging
            self.logger.error("Wikipedia search failed: %s", exc)
            return f"Entschuldigung, bei der Wikipedia-Suche zu '{lookup_term}' ist ein Fehler aufgetreten."

    def suggest_topics(self, partial_query: str, limit: int = 5) -> List[str]:
        """Return auto-complete suggestions for the GUI."""
        cleaned = self._normalize_query(partial_query)
        if not cleaned:
            return []

        params = {
            "action": "opensearch",
            "search": cleaned,
            "namespace": 0,
            "limit": limit,
            "format": "json",
        }
        data = self._request_json(self.api_url, params=params)
        if not data or len(data) < 2:
            return []
        return [entry for entry in data[1] if isinstance(entry, str)]

    def check_availability(self) -> bool:
        params = {
            "action": "query",
            "meta": "siteinfo",
            "format": "json",
        }
        data = self._request_json(self.api_url, params=params)
        return bool(data and data.get("query", {}).get("general"))

    def close(self) -> None:
        if self.session:
            self.session.close()
            self.logger.info("Wikipedia plugin session closed")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _normalize_query(self, query: str) -> str:
        text = (query or "").strip().lower()
        if not text:
            return ""

        replacements = {0x00E4: "ae", 0x00F6: "oe", 0x00FC: "ue", 0x00DF: "ss"}
        text = text.translate(replacements)

        fillers = [
            "suche nach ",
            "suche ",
            "finde ",
            "infos ueber ",
            "infos uber ",
            "infos ueber",
            "infos uber",
            "infos ",
            "information ueber ",
            "informationen ueber ",
            "information uber ",
            "informationen uber ",
            "was ist ",
            "wer ist ",
            "zu ",
        ]

        stripped = True
        while stripped and text:
            stripped = False
            for prefix in fillers:
                if text.startswith(prefix):
                    text = text[len(prefix):]
                    stripped = True
                    break

        if text.startswith("ueber "):
            text = text[len("ueber "):]

        return " ".join(part for part in text.split() if part)

    def _resolve_title(self, title: str) -> Optional[str]:
        params = {
            "action": "query",
            "titles": title,
            "prop": "info",
            "redirects": 1,
            "converttitles": 1,
            "format": "json",
        }
        data = self._request_json(self.api_url, params=params)
        if not data:
            return None

        query_block = data.get("query", {})
        redirects = query_block.get("redirects", [])
        normalized = query_block.get("normalized", [])

        resolved_title = title
        if normalized:
            resolved_title = normalized[-1].get("to", resolved_title)
        if redirects:
            resolved_title = redirects[-1].get("to", resolved_title)

        pages = query_block.get("pages", {})
        for page in pages.values():
            if "missing" not in page:
                return page.get("title", resolved_title)

        return resolved_title

    def _search_articles(self, query: str, max_results: int = 5) -> List[str]:
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srwhat": "nearmatch",
            "srinfo": "totalhits",
            "srprop": "snippet",
            "srlimit": max_results,
            "format": "json",
        }
        data = self._request_json(self.api_url, params=params)
        if not data:
            return []

        search_hits = data.get("query", {}).get("search", [])
        titles = []
        for hit in search_hits:
            title = hit.get("title")
            if not isinstance(title, str):
                continue
            titles.append(title)
        return titles

    def _pick_best_match(self, query: str, titles: List[str]) -> str:
        lower_query = query.lower()
        for title in titles:
            if title.lower() == lower_query:
                return title
        for title in titles:
            if title.lower().startswith(lower_query):
                return title
        for title in titles:
            padded = f" {title.lower()} "
            if f" {lower_query} " in padded:
                return title
        return titles[0]

    def _get_article_summary(self, title: str) -> Optional[str]:
        url = f"{self.base_url}/page/summary/{quote(title, safe='')}"
        data = self._request_json(url)
        if not data:
            return None

        if data.get("type", "").endswith("/not_found"):
            return None

        summary_title = data.get("title", title)
        extract = data.get("extract") or data.get("description")
        if not extract:
            return None

        condensed = condense_text(extract, min_length=220, max_length=780)
        suggestions = data.get("titles", {})
        display_title = suggestions.get("normalized") if isinstance(suggestions, dict) else None
        chosen_title = display_title or summary_title
        return self._format_result(chosen_title, condensed)

    def _format_result(self, title: str, body: str, suggestions: Optional[List[str]] = None) -> str:
        lines = [f"Wikipedia-Information zu '{title}':", "", body]
        if suggestions:
            filtered = [entry for entry in suggestions if entry and entry != title]
            if filtered:
                lines.append("")
                lines.append("Weitere verwandte Artikel:")
                for entry in filtered:
                    lines.append(f"- {entry}")
        return "\n".join(lines)

    def _request_json(self, url: str, params: Optional[Dict[str, str]] = None) -> Optional[dict]:
        request_key = self._build_request_key(url, params)
        for attempt in range(self.max_retries):
            cooldown_until = self._penalized_requests.get(request_key, 0.0)
            now = time.monotonic()
            if now < cooldown_until:
                remaining = round(cooldown_until - now, 2)
                self.logger.warning("Wikipedia-Anfrage wird fuer %.2fs blockiert: %s", remaining, url)
                return None
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
            except requests.RequestException as exc:
                self.logger.warning("Wikipedia request failed (attempt %s/%s): %s", attempt + 1, self.max_retries, exc)
                if attempt + 1 == self.max_retries:
                    self._penalized_requests[request_key] = time.monotonic() + self.retry_backoff * 4
                    return None
                time.sleep(self.retry_backoff * (attempt + 1))
                continue

            status = response.status_code
            if status == 404:
                self.logger.info("Wikipedia meldet 404 fuer %s (%s)", response.url, params or {})
                self._penalized_requests[request_key] = time.monotonic() + self.failure_cooldown
                return None
            if 400 <= status < 500:
                snippet = response.text[:180] if response.text else ""
                self.logger.warning("Wikipedia HTTP %s fuer %s: %s", status, response.url, snippet)
                self._penalized_requests[request_key] = time.monotonic() + self.failure_cooldown
                return None
            if status >= 500:
                self.logger.warning("Wikipedia HTTP %s fuer %s (attempt %s/%s)", status, response.url, attempt + 1, self.max_retries)
                if attempt + 1 == self.max_retries:
                    self._penalized_requests[request_key] = time.monotonic() + self.retry_backoff * 4
                    return None
                time.sleep(self.retry_backoff * (attempt + 1))
                continue

            try:
                return response.json()
            except ValueError as exc:
                self.logger.error("Wikipedia response could not be decoded: %s", exc)
                self._penalized_requests[request_key] = time.monotonic() + self.retry_backoff * 3
                return None

        self._penalized_requests[request_key] = time.monotonic() + self.retry_backoff * 4
        return None

    def _build_request_key(self, url: str, params: Optional[Dict[str, str]]) -> str:
        if not params:
            return url
        try:
            parts = [f"{key}={params[key]}" for key in sorted(params.keys())]
        except Exception:
            parts = []
        payload = "&".join(parts)
        return f"{url}?{payload}".lower()


if __name__ == "__main__":  # pragma: no cover - manual smoke test
    plugin = WikipediaPlugin()
    try:
        print(plugin.search("Nvidia"))
    finally:
        plugin.close()


