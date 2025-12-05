"""
Zentrale Verwaltung für das Gedächtnissystem von J.A.R.V.I.S.
Bündelt Kurzzeit- und Langzeitgedächtnis in einer einheitlichen Schnittstelle.
"""

import json
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
import logging
import uuid
from pathlib import Path
import os
import requests

from .short_term import ShortTermMemory
from .long_term import LongTermMemory
from .vector import VectorMemory
from .timeline import TimelineMemory
from utils.text_shortener import condense_text

logger = logging.getLogger(__name__)


class MemoryServiceClient:
    """HTTP-Client fuer den Go-basierten memoryd-Service."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        token: Optional[str] = None,
        *,
        timeout: float = 5.0,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        env_disable = os.getenv("JARVIS_MEMORYD_ENABLED")
        disable_flag = env_disable is not None and env_disable.strip().lower() in {"0", "false", "no"}
        chosen_url = base_url or os.getenv("JARVIS_MEMORYD_URL") or "http://127.0.0.1:7072"
        if disable_flag:
            chosen_url = ""
        self.base_url = chosen_url.rstrip("/") if chosen_url else ""
        self.token = token or os.getenv("JARVIS_MEMORYD_TOKEN") or os.getenv("MEMORYD_TOKEN")
        self.timeout = timeout
        self.enabled = bool(self.base_url)
        self.logger = logger or logging.getLogger(__name__)
        self.session = requests.Session()

    @classmethod
    def from_env(cls, settings: Optional[Dict[str, Any]] = None, logger: Optional[logging.Logger] = None) -> "MemoryServiceClient":
        cfg = settings or {}
        go_cfg = cfg.get("go_services") or {}
        mem_cfg = go_cfg.get("memoryd") if isinstance(go_cfg, dict) else {}
        base_url = None
        token = None
        timeout = 5.0
        if isinstance(mem_cfg, dict):
            base_url = mem_cfg.get("base_url") or mem_cfg.get("url")
            token = mem_cfg.get("token") or mem_cfg.get("api_key")
            timeout = float(mem_cfg.get("timeout_seconds", timeout))
        return cls(base_url=base_url, token=token, timeout=timeout, logger=logger)

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["X-API-Key"] = self.token
        return headers

    def save(self, key: str, value: Any, *, category: str = "", tags: Optional[List[str]] = None, importance: float = 0.0, expires_at: Optional[datetime] = None) -> bool:
        if not self.enabled:
            return False
        payload: Dict[str, Any] = {
            "key": key,
            "value": value,
            "category": category,
            "tags": tags or [],
            "importance": importance,
        }
        if expires_at:
            payload["expires_at"] = expires_at.isoformat()
        try:
            resp = self.session.post(f"{self.base_url}/memory/save", json=payload, headers=self._headers(), timeout=self.timeout)
            return bool(resp.ok)
        except Exception as exc:
            self.logger.debug("memoryd save fehlgeschlagen: %s", exc)
            return False

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        if not self.enabled:
            return None
        try:
            resp = self.session.get(f"{self.base_url}/memory/get", params={"key": key}, headers=self._headers(), timeout=self.timeout)
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            self.logger.debug("memoryd get fehlgeschlagen: %s", exc)
            return None

    def delete(self, key: str) -> bool:
        if not self.enabled:
            return False
        try:
            resp = self.session.delete(f"{self.base_url}/memory/delete", json={"key": key}, headers=self._headers(), timeout=self.timeout)
            return bool(resp.ok)
        except Exception as exc:
            self.logger.debug("memoryd delete fehlgeschlagen: %s", exc)
            return False

    def search(self, query: str, *, category: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        if not self.enabled:
            return []
        payload = {"query": query, "limit": limit}
        if category:
            payload["category"] = category
        try:
            resp = self.session.post(f"{self.base_url}/memory/search", json=payload, headers=self._headers(), timeout=self.timeout)
            resp.raise_for_status()
            body = resp.json() or {}
            results = body.get("results") or []
            if isinstance(results, list):
                return results
        except Exception as exc:
            self.logger.debug("memoryd search fehlgeschlagen: %s", exc)
        return []

class MemoryManager:
    """Zentrale Klasse zur Verwaltung von Kurzzeit- und Langzeitgedächtnis."""
    
    def __init__(self, data_dir: str = "data"):
        """Initialisiert den MemoryManager.
        
        Args:
            data_dir: Verzeichnis für die Speicherung der Gedächtnisdaten
        """
        # Verzeichnis für die Speicherung erstellen
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Komponenten initialisieren
        self.short_term = ShortTermMemory()
        self.long_term = LongTermMemory(storage_file=str(self.data_dir / "long_term_memory.json"))
        try:
            self.vector_memory = VectorMemory(storage_file=str(self.data_dir / "vector_memory.json"))
        except Exception as exc:
            logger.warning("VectorMemory konnte nicht initialisiert werden: %s", exc)
            self.vector_memory = None
        try:
            self.timeline_memory = TimelineMemory(storage_file=str(self.data_dir / "timeline_memory.json"))
        except Exception as exc:
            logger.warning("TimelineMemory konnte nicht initialisiert werden: %s", exc)
            self.timeline_memory = None
        
        self.memoryd_client = MemoryServiceClient.from_env(logger=logger)

        # Konversationsverlauf und Kontext
        self.conversation_history: List[Dict[str, Any]] = []
        self.current_context: Dict[str, Any] = {}
        self.active_topics: Set[str] = set()  # Aktive Themen im aktuellen Gespräch
        self._load_previous_topics()
    
    # Rest der Implementierung bleibt gleich...
    # (Platzersparnis - volle Implementierung bereits in der Datei)
