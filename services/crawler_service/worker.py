"""Worker threads for the crawler service."""

from __future__ import annotations

import queue
import threading
import time
from dataclasses import dataclass, field
from typing import Dict, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse, urldefrag

import requests
from bs4 import BeautifulSoup

try:
    from langdetect import detect  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    detect = None  # type: ignore

from .config import CrawlerConfig
from .models import JobStatus
from . import storage
from .security_guard import SecurityGuard


@dataclass
class JobRuntime:
    max_pages: int
    max_depth: int
    topic: str
    processed: int = 0
    pending: int = 0
    visited: Set[str] = field(default_factory=set)
    active: bool = True


class CrawlerWorker:
    """Manages crawler job queue and worker threads."""

    def __init__(self, config: CrawlerConfig, guard: SecurityGuard) -> None:
        self.config = config
        self.guard = guard
        self.queue: queue.Queue[Tuple[int, str, int]] = queue.Queue()
        self.stop_event = threading.Event()
        self.running_event = threading.Event()
        self.running_event.set()
        self.threads: list[threading.Thread] = []
        self.job_state: Dict[int, JobRuntime] = {}
        self.state_lock = threading.Lock()

    def start(self) -> None:
        if self.threads:
            return
        for idx in range(self.config.max_workers):
            thread = threading.Thread(target=self._worker_loop, name=f"CrawlerWorker-{idx}", daemon=True)
            thread.start()
            self.threads.append(thread)

    def stop(self) -> None:
        self.stop_event.set()
        self.running_event.set()
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except queue.Empty:
                break
        for thread in self.threads:
            thread.join(timeout=2.0)
        self.threads.clear()

    def pause(self) -> None:
        self.running_event.clear()

    def resume(self) -> None:
        self.running_event.set()

    def enqueue_job(self, job) -> None:
        runtime = JobRuntime(max_pages=job.max_pages, max_depth=job.max_depth, topic=job.topic, processed=job.processed_pages)
        with self.state_lock:
            self.job_state[job.id] = runtime
        for start_url in job.start_urls:
            self._schedule_url(job.id, start_url, depth=0)
        storage.update_job_status(job.id, status=JobStatus.RUNNING, processed_pages=job.processed_pages)

    def _worker_loop(self) -> None:
        while not self.stop_event.is_set():
            if not self.running_event.is_set():
                self.running_event.wait(timeout=0.5)
                continue
            try:
                job_id, url, depth = self.queue.get(timeout=0.5)
            except queue.Empty:
                self._maybe_finalize_jobs()
                continue
            state = self.job_state.get(job_id)
            if not state or not state.active:
                self.queue.task_done()
                continue
            with self.state_lock:
                state.pending = max(0, state.pending - 1)
            try:
                self._process(job_id, url, depth, state)
            finally:
                self.queue.task_done()
                self._maybe_finalize_jobs()

    def _process(self, job_id: int, url: str, depth: int, state: JobRuntime) -> None:
        if depth > state.max_depth:
            return
        if state.processed >= state.max_pages:
            return
        if not self.guard.check_resources():
            time.sleep(1.5)
            self._schedule_url(job_id, url, depth, force=True)
            return
        parsed = urlparse(url)
        if not self.guard.check_domain(url):
            return
        if not self.guard.check_rate_limit(parsed.netloc):
            time.sleep(2.0)
            self._schedule_url(job_id, url, depth, force=True)
            return
        if not self.guard.allowed_by_robots(url):
            return
        headers = {"User-Agent": self.config.network.user_agent}
        try:
            response = requests.get(url, headers=headers, timeout=15)
        except Exception:
            return
        if response.status_code >= 400:
            return
        content_type = response.headers.get("Content-Type", "")
        if "text/html" not in content_type:
            return
        soup = BeautifulSoup(response.text, "lxml")
        title = (soup.title.string.strip() if soup.title and soup.title.string else "")[:500]
        text = soup.get_text(" ", strip=True)
        if not text:
            return
        language = self._detect_language(text)
        domain = parsed.netloc
        doc_id = storage.add_document(
            job_id=job_id,
            url=url,
            title=title,
            text=text,
            lang=language,
            domain=domain,
        )
        if doc_id:
            processed = storage.increment_processed_pages(job_id, 1)
            with self.state_lock:
                state.processed = processed
        if state.processed >= state.max_pages:
            return
        self._enqueue_links(job_id, url, depth, soup, state)

    def _detect_language(self, text: str) -> str:
        if detect is None:
            return ""
        try:
            lang = detect(text[:5000])
            if lang in {"de", "en"}:
                return lang
            return lang
        except Exception:
            return ""

    def _enqueue_links(self, job_id: int, base_url: str, depth: int, soup: BeautifulSoup, state: JobRuntime) -> None:
        next_depth = depth + 1
        if next_depth > state.max_depth:
            return
        for anchor in soup.find_all("a", href=True):
            href = anchor.get("href", "").strip()
            if not href or href.startswith("#") or href.lower().startswith("javascript:"):
                continue
            new_url = urljoin(base_url, href)
            clean_url, _frag = urldefrag(new_url)
            if not self.guard.check_domain(clean_url):
                continue
            self._schedule_url(job_id, clean_url, next_depth)

    def _schedule_url(self, job_id: int, url: str, depth: int, force: bool = False) -> None:
        clean_url, _ = urldefrag(url)
        if not clean_url:
            return
        with self.state_lock:
            state = self.job_state.get(job_id)
            if not state or not state.active:
                return
            if depth > state.max_depth:
                return
            if clean_url in state.visited and not force:
                return
            if not force:
                state.visited.add(clean_url)
            state.pending += 1
            self.queue.put((job_id, clean_url, depth))

    def _maybe_finalize_jobs(self) -> None:
        with self.state_lock:
            for job_id, state in list(self.job_state.items()):
                if not state.active:
                    continue
                if state.processed >= state.max_pages or state.pending == 0:
                    state.active = False
                    storage.update_job_status(job_id, status=JobStatus.COMPLETED, processed_pages=state.processed)
