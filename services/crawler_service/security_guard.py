"""Security guard for crawler resource/network restrictions."""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from pathlib import Path
from typing import Deque, Dict, Optional
from urllib.parse import urlparse
from urllib import robotparser, request

import psutil

from .config import CrawlerConfig


class SecurityGuard:
    """Enforces domain, rate and resource limitations for crawler workers."""

    def __init__(self, config: CrawlerConfig) -> None:
        self.config = config
        self.allowed_domains = {self._normalize_domain(host) for host in config.network.allowed_domains}
        self.rate_buckets: Dict[str, Deque[float]] = defaultdict(deque)
        self.global_bucket: Deque[float] = deque()
        self.bucket_lock = threading.Lock()
        self._robots_parsers: Dict[str, robotparser.RobotFileParser] = {}
        self._robots_lock = threading.Lock()
        self.log_file = config.data_path / "crawler.log"
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _normalize_domain(hostname: str) -> str:
        host = (hostname or "").strip().lower()
        if host.startswith("www."):
            host = host[4:]
        return host

    def _log(self, tag: str, message: str) -> None:
        line = f"[CRAWLER][{tag}] {time.strftime('%Y-%m-%d %H:%M:%S')} {message}\n"
        try:
            self.log_file.open("a", encoding="utf-8").write(line)
        except Exception:
            pass

    def check_domain(self, url: str) -> bool:
        domain = self._normalize_domain(urlparse(url).netloc)
        if not domain:
            self._log("BLOCKED_DOMAIN", f"Invalid domain for URL {url}")
            return False
        if not self.allowed_domains:
            return True
        if domain in self.allowed_domains:
            return True
        for allowed in self.allowed_domains:
            if allowed and (domain == allowed or domain.endswith(f".{allowed}")):
                return True
        self._log("BLOCKED_DOMAIN", f"Domain not allowed: {domain}")
        return False

    def check_rate_limit(self, domain: str) -> bool:
        """Return True if request can proceed."""
        domain_key = self._normalize_domain(domain)
        now = time.monotonic()
        limit = max(1, self.config.network.max_requests_per_minute)
        with self.bucket_lock:
            self._purge_buckets(self.global_bucket, now)
            self._purge_buckets(self.rate_buckets[domain_key], now)
            if len(self.global_bucket) >= limit or len(self.rate_buckets[domain_key]) >= limit:
                self._log("RATE_LIMIT", f"Rate limit hit for domain {domain_key}")
                return False
            self.global_bucket.append(now)
            self.rate_buckets[domain_key].append(now)
        return True

    @staticmethod
    def _purge_buckets(bucket: Deque[float], now: float) -> None:
        window = 60.0
        while bucket and now - bucket[0] > window:
            bucket.popleft()

    def check_resources(self) -> bool:
        """Ensure CPU and memory usage stay below configured limits."""
        try:
            cpu_usage = psutil.cpu_percent(interval=None)
            if cpu_usage > self.config.resource_limits.max_cpu_percent:
                self._log("RESOURCES", f"CPU limit reached ({cpu_usage:.1f}%)")
                return False
            mem = psutil.virtual_memory()
            used_mb = (mem.total - mem.available) / (1024 * 1024)
            if used_mb > self.config.resource_limits.max_memory_mb:
                self._log("RESOURCES", f"Memory limit reached ({used_mb:.0f}MB)")
                return False
        except Exception as exc:
            self._log("RESOURCES", f"Resource check failed: {exc}")
            return False
        return True

    def allowed_by_robots(self, url: str) -> bool:
        if not self.config.network.respect_robots_txt:
            return True
        parsed = urlparse(url)
        domain = self._normalize_domain(parsed.netloc)
        if not domain:
            return False
        parser = self._get_robots_parser(parsed)
        if not parser:
            self._log("ROBOTS", f"No robots.txt data for {domain}; allowing requests")
            return True
        user_agent = self.config.network.user_agent or "JarvisCrawler"
        allowed = parser.can_fetch(user_agent, url)
        if not allowed:
            self._log("ROBOTS_BLOCK", f"robots.txt disallows {url}")
        return allowed

    def _get_robots_parser(self, parsed_url) -> Optional[robotparser.RobotFileParser]:
        domain = self._normalize_domain(parsed_url.netloc)
        with self._robots_lock:
            parser = self._robots_parsers.get(domain)
            if parser:
                return parser
            robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
            parser = robotparser.RobotFileParser()
            parser.set_url(robots_url)
            try:
                req = request.Request(robots_url, headers={"User-Agent": self.config.network.user_agent})
                with request.urlopen(req, timeout=10) as response:
                    parser.parse(response.read().decode("utf-8", errors="ignore").splitlines())
            except Exception as exc:
                self._log("ROBOTS", f"robots.txt fetch failed for {domain}: {exc}")
                return None
            self._robots_parsers[domain] = parser
            return parser
