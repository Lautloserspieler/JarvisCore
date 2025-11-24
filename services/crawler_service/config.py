"""Configuration helpers for the crawler service."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ResourceLimits:
    max_cpu_percent: int = 50
    max_memory_mb: int = 1024
    max_disk_write_mb_per_min: int = 50


@dataclass
class NetworkConfig:
    allowed_domains: List[str] = field(default_factory=list)
    max_requests_per_minute: int = 30
    respect_robots_txt: bool = True
    user_agent: str = "JarvisCrawler/0.1"


@dataclass
class CrawlerConfig:
    listen_host: str = "127.0.0.1"
    listen_port: int = 8090
    api_key: str = ""
    data_dir: str = "data/crawler"
    db_path: str = "data/crawler/crawler.db"
    max_workers: int = 1
    max_pages_per_job: int = 250
    max_depth: int = 2
    resource_limits: ResourceLimits = field(default_factory=ResourceLimits)
    network: NetworkConfig = field(default_factory=NetworkConfig)

    @property
    def data_path(self) -> Path:
        return Path(self.data_dir).expanduser().resolve()

    @property
    def db_file(self) -> Path:
        db_path = Path(self.db_path)
        if not db_path.is_absolute():
            return (self.data_path / db_path.name).resolve()
        return db_path


def _build_config(payload: Dict[str, Any]) -> CrawlerConfig:
    resource_cfg = payload.get("resource_limits") or {}
    network_cfg = payload.get("network") or {}
    config = CrawlerConfig(
        listen_host=str(payload.get("listen_host", "127.0.0.1")),
        listen_port=int(payload.get("listen_port", 8090)),
        api_key=str(payload.get("api_key", "")),
        data_dir=str(payload.get("data_dir", "data/crawler")),
        db_path=str(payload.get("db_path", "data/crawler/crawler.db")),
        max_workers=max(1, int(payload.get("max_workers", 1))),
        max_pages_per_job=max(1, int(payload.get("max_pages_per_job", 250))),
        max_depth=max(0, int(payload.get("max_depth", 1))),
        resource_limits=ResourceLimits(
            max_cpu_percent=int(resource_cfg.get("max_cpu_percent", 50)),
            max_memory_mb=int(resource_cfg.get("max_memory_mb", 1024)),
            max_disk_write_mb_per_min=int(resource_cfg.get("max_disk_write_mb_per_min", 50)),
        ),
        network=NetworkConfig(
            allowed_domains=[str(item).strip().lower() for item in network_cfg.get("allowed_domains", []) if item],
            max_requests_per_minute=int(network_cfg.get("max_requests_per_minute", 30)),
            respect_robots_txt=bool(network_cfg.get("respect_robots_txt", True)),
            user_agent=str(network_cfg.get("user_agent", "JarvisCrawler/0.1")),
        ),
    )
    return config


def load_config(path: Optional[str | Path] = None) -> CrawlerConfig:
    """Load crawler configuration from disk."""
    cfg_path = Path(path) if path else Path("services/crawler_service/config_crawler.json")
    payload: Dict[str, Any] = {}
    if cfg_path.exists():
        payload = json.loads(cfg_path.read_text(encoding="utf-8"))
    config = _build_config(payload)
    config.data_path.mkdir(parents=True, exist_ok=True)
    config.db_file.parent.mkdir(parents=True, exist_ok=True)
    return config
