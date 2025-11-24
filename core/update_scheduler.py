"""
Background scheduler for knowledge/model updates.
"""

from __future__ import annotations

import threading
import time
from datetime import datetime, timedelta
from typing import Optional, Dict

from utils.logger import Logger


class UpdateScheduler:
    """Periodically refreshes knowledge caches and checks LLM models."""

    def __init__(
        self,
        knowledge_manager,
        learning_manager,
        llm_manager=None,
        long_term_trainer=None,
        interval_hours: float = 6.0,
        crawler_client=None,
        crawler_sync_interval: Optional[int] = None,
    ):
        self.knowledge_manager = knowledge_manager
        self.learning_manager = learning_manager
        self.llm_manager = llm_manager
        self.long_term_trainer = long_term_trainer
        self.interval = max(1.0, float(interval_hours))
        self.logger = Logger()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._crawler_lock = threading.Lock()
        self.crawler_client = crawler_client
        self._crawler_sync_interval = None
        if crawler_sync_interval:
            self._crawler_sync_interval = max(60, int(crawler_sync_interval))
        elif getattr(crawler_client, "config", None):
            try:
                self._crawler_sync_interval = max(60, int(getattr(crawler_client.config, "sync_interval_sec", 1800)))
            except Exception:
                self._crawler_sync_interval = 1800
        self._next_update_at: Optional[float] = None
        self._next_crawler_sync_at: Optional[float] = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        now = time.time()
        self._next_update_at = now
        if self._crawler_enabled():
            self._next_crawler_sync_at = now + (self._crawler_sync_interval or 1800)
        self._thread = threading.Thread(target=self._run, name="JarvisUpdateScheduler", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._thread = None

    def _run(self) -> None:
        while not self._stop_event.is_set():
            now = time.time()
            if self._next_update_at is None or now >= self._next_update_at:
                self._perform_update()
                self._next_update_at = now + self.interval * 3600
            if self._crawler_enabled():
                if self._next_crawler_sync_at is None or now >= self._next_crawler_sync_at:
                    self._run_crawler_sync()
                    self._next_crawler_sync_at = now + (self._crawler_sync_interval or 1800)
            else:
                self._next_crawler_sync_at = None
            targets = [self._next_update_at]
            if self._next_crawler_sync_at:
                targets.append(self._next_crawler_sync_at)
            wait_candidates = [target - time.time() for target in targets if target]
            timeout = min(wait_candidates) if wait_candidates else 5.0
            timeout = max(0.5, min(timeout, 300.0))
            self._stop_event.wait(timeout)

    def _perform_update(self) -> None:
        try:
            self.logger.info("Automatisches Wissens-Update wird gestartet")
            if hasattr(self.knowledge_manager, "refresh_local_knowledge"):
                self.knowledge_manager.refresh_local_knowledge(blocking=False)
            if hasattr(self.knowledge_manager, "cleanup_old_cache"):
                self.knowledge_manager.cleanup_old_cache()
            self.learning_manager.mark_update("knowledge")
        except Exception as exc:
            self.logger.warning(f"Automatisches Wissens-Update fehlgeschlagen: {exc}")
        try:
            if hasattr(self.learning_manager, "run_retraining"):
                retrain_result = self.learning_manager.run_retraining()
                if retrain_result is not None:
                    self.logger.info("Reinforcement-Retraining ausgefuehrt: %s", retrain_result)
        except Exception as exc:
            self.logger.warning(f"Reinforcement-Retraining fehlgeschlagen: {exc}")
        try:
            if self.llm_manager and hasattr(self.llm_manager, "auto_install_models"):
                self.logger.info("Pruefe LLM-Modelle auf Updates")
                self.llm_manager.auto_install_models()
                self.learning_manager.mark_update("models")
        except Exception as exc:
            self.logger.warning(f"LLM-Check fehlgeschlagen: {exc}")
        try:
            if self.long_term_trainer:
                self.logger.info("Long-Term Trainer wird ausgefuehrt")
                result = self.long_term_trainer.run_cycle()
                if result:
                    self.learning_manager.mark_update("long_term_summary")
        except Exception as exc:
            self.logger.warning(f"Long-Term Trainer Fehler: {exc}")

    def _crawler_enabled(self) -> bool:
        if not (self.crawler_client and getattr(self.crawler_client, "is_enabled", lambda: False)() and self._crawler_sync_interval):
            return False
        config = getattr(self.crawler_client, "config", None)
        auto_sync_enabled = getattr(config, "auto_sync", True)
        return bool(auto_sync_enabled)

    def _run_crawler_sync(self, *, force: bool = False) -> Optional[Dict[str, int]]:
        if not force and not self._crawler_enabled():
            return None
        with self._crawler_lock:
            try:
                last_sync = None
                if hasattr(self.crawler_client, "load_last_sync"):
                    last_sync = self.crawler_client.load_last_sync()
                documents = self.crawler_client.sync_new_documents(last_sync)
                if not documents:
                    return {"documents": 0, "imported": 0}
                imported = 0
                if hasattr(self.knowledge_manager, "import_crawler_documents"):
                    imported = self.knowledge_manager.import_crawler_documents(documents)
                doc_ids = [doc["id"] for doc in documents if isinstance(doc.get("id"), int)]
                if doc_ids:
                    self.crawler_client.ack_documents(doc_ids)
                newest = max(
                    (
                        doc.get("created_at")
                        for doc in documents
                        if isinstance(doc.get("created_at"), (int, float))
                    ),
                    default=None,
                )
                if newest:
                    latest_dt = datetime.fromtimestamp(newest)
                    self.crawler_client.save_last_sync(latest_dt)
                self.logger.info("Crawler Sync importierte %s Dokumente", imported)
                return {"documents": len(documents), "imported": imported}
            except Exception as exc:
                self.logger.warning(f"Crawler Sync fehlgeschlagen: {exc}")
                return None

    def sync_crawler_now(self) -> Optional[Dict[str, int]]:
        """Expose crawler sync for manual triggers (e.g., Web-UI)."""
        return self._run_crawler_sync(force=True)
