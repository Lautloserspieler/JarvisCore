"""
HTTP client for the external crawler service.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from utils.logger import Logger


@dataclass
class CrawlerClientConfig:
    enabled: bool
    base_url: str
    api_key: str
    sync_interval_sec: int
    auto_sync: bool = True


class CrawlerClient:
    """Thin wrapper around the crawler service HTTP API."""

    def __init__(self, settings_path: Path | str = Path("data/settings.json")) -> None:
        self.settings_path = Path(settings_path)
        self.logger = Logger()
        self.session = requests.Session()
        self.config = self._load_config()
        self.state_path = Path("data/crawler_state.json")
        self.state_path.parent.mkdir(parents=True, exist_ok=True)

    def _load_config(self) -> CrawlerClientConfig:
        payload: Dict[str, Any] = {}
        if self.settings_path.exists():
            payload = json.loads(self.settings_path.read_text(encoding="utf-8"))
        crawler_cfg = payload.get("crawler") or {}
        return CrawlerClientConfig(
            enabled=bool(crawler_cfg.get("enabled", False)),
            base_url=str(crawler_cfg.get("base_url", "http://127.0.0.1:8090")).rstrip("/"),
            api_key=str(crawler_cfg.get("api_key", "")),
            sync_interval_sec=int(crawler_cfg.get("sync_interval_sec", 1800)),
            auto_sync=bool(crawler_cfg.get("auto_sync", True)),
        )

    def refresh_config(self) -> None:
        self.config = self._load_config()

    def is_enabled(self) -> bool:
        return self.config.enabled and bool(self.config.api_key)

    def start_topic_job(
        self,
        topic: str,
        start_urls: List[str],
        max_pages: int,
        max_depth: int,
    ) -> Optional[int]:
        if not self.is_enabled():
            self.logger.info("Crawler client disabled, skipping job creation")
            return None
        payload = {
            "topic": topic,
            "start_urls": start_urls,
            "max_pages": max_pages,
            "max_depth": max_depth,
        }
        response = self._request("POST", "/jobs", json=payload)
        if not response:
            return None
        data = response.json()
        return int(data.get("job_id"))

    def list_jobs(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        if not self.is_enabled():
            return []
        params = {"status": status} if status else None
        response = self._request("GET", "/jobs", params=params)
        if not response:
            return []
        return response.json()

    def get_job_status(self, job_id: int) -> Optional[Dict[str, Any]]:
        if not self.is_enabled():
            return None
        response = self._request("GET", f"/jobs/{job_id}/status")
        if not response:
            return None
        return response.json()

    def sync_new_documents(self, since_timestamp: Optional[datetime] = None) -> List[Dict[str, Any]]:
        if not self.is_enabled():
            return []
        params: Dict[str, Any] = {}
        if since_timestamp:
            params["since"] = since_timestamp.isoformat()
        response = self._request("GET", "/results", params=params)
        if not response:
            return []
        return response.json()

    def ack_documents(self, doc_ids: List[int]) -> bool:
        if not self.is_enabled() or not doc_ids:
            return False
        response = self._request("POST", "/results/ack", json={"ids": doc_ids})
        return bool(response and response.ok)

    def pause_workers(self) -> bool:
        if not self.is_enabled():
            return False
        response = self._request("POST", "/control/pause")
        return bool(response and response.ok)

    def resume_workers(self) -> bool:
        if not self.is_enabled():
            return False
        response = self._request("POST", "/control/resume")
        return bool(response and response.ok)

    def get_health(self) -> Optional[Dict[str, Any]]:
        if not self.is_enabled():
            return None
        response = self._request("GET", "/health")
        if not response:
            return None
        try:
            return response.json()
        except Exception:
            return None

    def load_last_sync(self) -> Optional[datetime]:
        if not self.state_path.exists():
            return None
        try:
            data = json.loads(self.state_path.read_text(encoding="utf-8"))
            last_sync = data.get("last_sync")
            if isinstance(last_sync, (int, float)):
                return datetime.fromtimestamp(last_sync)
            if isinstance(last_sync, str):
                return datetime.fromisoformat(last_sync)
        except Exception as exc:
            self.logger.warning(f"Crawler state file invalid: {exc}")
        return None

    def save_last_sync(self, timestamp: datetime) -> None:
        payload = {"last_sync": timestamp.isoformat()}
        self.state_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _request(self, method: str, path: str, **kwargs) -> Optional[requests.Response]:
        url = f"{self.config.base_url}{path}"
        headers = kwargs.pop("headers", {})
        headers["X-API-Key"] = self.config.api_key
        try:
            response = self.session.request(method, url, headers=headers, timeout=20, **kwargs)
            response.raise_for_status()
            return response
        except Exception as exc:
            self.logger.warning(f"Crawler request {method} {url} failed: {exc}")
            return None
