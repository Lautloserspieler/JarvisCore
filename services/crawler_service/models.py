"""Data models shared across crawler modules."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


class JobStatus:
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"

    TERMINAL_STATES = {COMPLETED, FAILED}


@dataclass
class CrawlerJob:
    id: int
    topic: str
    start_urls: List[str]
    status: str
    max_pages: int
    max_depth: int
    created_at: datetime
    processed_pages: int = 0

    @classmethod
    def from_row(cls, row: Dict[str, Any]) -> "CrawlerJob":
        payload = dict(row)
        start_urls: List[str] = []
        raw_urls = payload.get("start_urls")
        if isinstance(raw_urls, str):
            try:
                parsed = json.loads(raw_urls)
                if isinstance(parsed, list):
                    start_urls = [str(item) for item in parsed if item]
            except json.JSONDecodeError:
                start_urls = [url.strip() for url in raw_urls.split(",") if url.strip()]
        created_at_raw = payload.get("created_at")
        created_at = datetime.fromisoformat(created_at_raw) if isinstance(created_at_raw, str) else datetime.utcnow()
        return cls(
            id=int(payload.get("id", 0)),
            topic=str(payload.get("topic", "")),
            start_urls=start_urls,
            status=str(payload.get("status", JobStatus.PENDING)),
            max_pages=int(payload.get("max_pages", 0)),
            max_depth=int(payload.get("max_depth", 0)),
            created_at=created_at,
            processed_pages=int(payload.get("processed_pages", 0)),
        )


@dataclass
class CrawledDocument:
    id: int
    job_id: int
    url: str
    title: str
    text: str
    lang: str
    domain: str
    created_at: datetime
    synced: bool = False
    crawl_topic: Optional[str] = None

    @classmethod
    def from_row(cls, row: Dict[str, Any]) -> "CrawledDocument":
        created_at_raw = row.get("created_at")
        created_at = datetime.fromisoformat(created_at_raw) if isinstance(created_at_raw, str) else datetime.utcnow()
        return cls(
            id=int(row.get("id", 0)),
            job_id=int(row.get("job_id", 0)),
            url=str(row.get("url", "")),
            title=str(row.get("title") or ""),
            text=str(row.get("text") or ""),
            lang=str(row.get("lang") or ""),
            domain=str(row.get("domain") or ""),
            created_at=created_at,
            synced=bool(row.get("synced", 0)),
            crawl_topic=row.get("topic"),
        )
