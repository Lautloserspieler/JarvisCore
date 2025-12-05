"""
Zentrale Verwaltung fÃ¼r das GedÃ¤chtnissystem von J.A.R.V.I.S.
BÃ¼ndelt Kurzzeit- und LangzeitgedÃ¤chtnis in einer einheitlichen Schnittstelle.
"""

import json

from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
import logging
import uuid
from pathlib import Path
import os
import requests

from .short_term_memory import ShortTermMemory
from .long_term_memory import LongTermMemory
from .vector_memory import VectorMemory
from .timeline_memory import TimelineMemory
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
    """Zentrale Klasse zur Verwaltung von Kurzzeit- und LangzeitgedÃ¤chtnis."""
    
    def __init__(self, data_dir: str = "data"):
        """Initialisiert den MemoryManager.
        
        Args:
            data_dir: Verzeichnis fÃ¼r die Speicherung der GedÃ¤chtnisdaten
        """
        # Verzeichnis fÃ¼r die Speicherung erstellen
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
        self.active_topics: Set[str] = set()  # Aktive Themen im aktuellen GesprÃ¤ch
        self._load_previous_topics()
    
    # --- KurzzeitgedÃ¤chtnis-Methoden ---
    
    def add_to_conversation(self, role: str, content: str, **metadata) -> None:
        """FÃ¼gt eine Nachricht zur aktuellen Konversation hinzu.
        
        Args:
            role: Rolle des Sprechers ('user' oder 'assistant')
            content: Inhalt der Nachricht
            **metadata: ZusÃ¤tzliche Metadaten (z.B. timestamp, command_type, topics)
        """
        metadata = dict(metadata)
        # Extrahiere Themen, falls vorhanden
        topics = metadata.pop('topics', None)
        timestamp = metadata.get('timestamp')
        
        # FÃ¼ge zum KurzzeitgedÃ¤chtnis hinzu
        self.short_term.add_context(role, content, timestamp=timestamp, topics=topics)
        
        # FÃ¼ge zum Konversationsverlauf hinzu
        entry = {
            'id': str(uuid.uuid4()),
            'role': role,
            'content': content,
            'timestamp': timestamp or datetime.now().isoformat(),
            'topics': list(topics) if topics else [],
            **{k: v for k, v in metadata.items() if k != 'timestamp' and k != 'topics'}
        }
        self.conversation_history.append(entry)
        
        # Aktive Themen aktualisieren
        if topics:
            self.active_topics.update(topics)
        
        # Aktualisiere den aktuellen Kontext
        self._update_current_context(entry)

        importance = float(metadata.get('importance', 0.5) or 0.5)
        if self.timeline_memory:
            try:
                meta_payload = {
                    k: str(v)
                    for k, v in metadata.items()
                    if k not in ('timestamp', 'importance')
                }
                self.timeline_memory.add_event(
                    "conversation",
                    {
                        "role": role,
                        "content": content,
                        "topics": list(topics) if topics else [],
                        "metadata": meta_payload,
                    },
                    timestamp=entry['timestamp'],
                    importance=importance,
                )
            except Exception:
                logger.debug("TimelineMemory konnte Konversationseintrag nicht speichern", exc_info=True)

        if self.vector_memory and role == 'user':
            try:
                vector_meta = {
                    "role": role,
                    "topics": ",".join(entry.get("topics", [])),
                }
                if 'intent' in metadata:
                    vector_meta['intent'] = str(metadata['intent'])
                if 'command_type' in metadata:
                    vector_meta['command_type'] = str(metadata['command_type'])
                self.vector_memory.add_entry(
                    content,
                    metadata=vector_meta,
                    importance=importance,
                )
            except Exception:
                logger.debug("VectorMemory konnte Benutzertext nicht speichern", exc_info=True)
    
    def get_conversation_context(self, max_messages: int = 5, include_topics: bool = True) -> str:
        """Gibt den aktuellen Konversationskontext zurÃ¼ck.
        
        Args:
            max_messages: Maximale Anzahl zurÃ¼ckzugebender Nachrichten
            include_topics: Ob Themeninformationen eingeschlossen werden sollen
            
        Returns:
            Formatierter Konversationsverlauf mit optionalen Themen
        """
        messages = self.conversation_history[-max_messages:]
        
        if not include_topics:
            return "\n".join(
                f"{msg['role'].capitalize()}: {msg['content']}" 
                for msg in messages
            )
        
        # FÃ¼ge Themeninformationen hinzu
        context = []
        if self.active_topics:
            context.append(f"Aktive Themen: {', '.join(sorted(self.active_topics))}")
            context.append("-" * 40)
            
        for msg in messages:
            speaker = msg['role'].capitalize()
            time_str = datetime.fromisoformat(msg['timestamp']).strftime('%H:%M')
            topics_info = f" [Themen: {', '.join(msg.get('topics', []))}]" if msg.get('topics') else ""
            context.append(f"[{time_str}] {speaker}: {msg['content']}{topics_info}")
            
        return "\n".join(context)
    
    def get_short_term_summary(self) -> str:
        """Gibt eine Zusammenfassung der aktuellen Konversation zurÃ¼ck."""
        return self.short_term.get_conversation_summary()
    


    # --- Erweiterte Gedaechtnisschichten ---

    def store_vector_memory(
        self,
        text: str,
        *,
        metadata: Optional[Dict[str, Any]] = None,
        importance: float = 0.5,
    ) -> Optional[str]:
        """Speichert einen Eintrag im semantischen Vektorspeicher."""
        if not getattr(self, 'vector_memory', None) or not text:
            return None
        try:
            return self.vector_memory.add_entry(
                text,
                metadata=metadata or {},
                importance=importance,
            )
        except Exception:
            logger.debug("VectorMemory konnte Eintrag nicht speichern", exc_info=True)
            return None

    def search_vector_memory(self, query: str, *, top_k: int = 5) -> List[Dict[str, Any]]:
        """Durchsucht den Vektorspeicher nach semantisch aehnlichen Erinnerungen."""
        if not getattr(self, 'vector_memory', None) or not query:
            return []
        try:
            return self.vector_memory.search(query, top_k=top_k)
        except Exception:
            logger.debug("VectorMemory Suche fehlgeschlagen", exc_info=True)
            return []

    def record_timeline_event(
        self,
        event_type: str,
        payload: Optional[Dict[str, Any]] = None,
        *,
        timestamp: Optional[str] = None,
        importance: float = 0.5,
    ) -> bool:
        """Speichert ein Ereignis im Zeitstrahl."""
        if not getattr(self, 'timeline_memory', None):
            return False
        try:
            self.timeline_memory.add_event(
                event_type,
                payload or {},
                timestamp=timestamp,
                importance=importance,
            )
            return True
        except Exception:
            logger.debug("TimelineMemory konnte Ereignis nicht speichern", exc_info=True)
            return False

    def query_timeline(
        self,
        *,
        event_type: Optional[str] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
        limit: int = 50,
        search_text: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Liefert Ereignisse aus dem Zeitstrahl."""
        if not getattr(self, 'timeline_memory', None):
            return []
        try:
            return self.timeline_memory.query(
                event_type=event_type,
                start=start,
                end=end,
                limit=limit,
                search_text=search_text,
            )
        except Exception:
            logger.debug("TimelineMemory Abfrage fehlgeschlagen", exc_info=True)
            return []

    # --- LangzeitgedÃ¤chtnis-Methoden ---
    
    def remember(self, key: str, value: Any, category: str = "general", 
                expires: Optional[datetime] = None, importance: int = 5,
                topics: Optional[List[str]] = None, source: str = "user") -> bool:
        """Speichert eine Information im LangzeitgedÃ¤chtnis.
        
        Args:
            key: Eindeutiger SchlÃ¼ssel fÃ¼r die Information
            value: Zu speichernder Wert
            category: Kategorie fÃ¼r die Organisation (z.B. 'projekt', 'erinnerung', 'alltag')
            expires: Optionales Ablaufdatum
            importance: Wichtigkeit der Information (1-10)
            topics: Liste von Themen, die mit dieser Erinnerung verknÃ¼pft sind
            source: Quelle der Information ('user', 'system', 'conversation')
            
        Returns:
            True bei Erfolg, sonst False
        """
        # FÃ¼ge aktive Themen hinzu, falls keine expliziten Themen angegeben wurden
        if not topics and self.active_topics:
            topics = list(self.active_topics)
            

        success = self.long_term.remember(
            key=key,
            value=value,
            category=category,
            expires=expires,
            importance=importance,
            topics=topics,
            source=source
        )
        if success:
            # Optional an Go-memoryd spiegeln
            try:
                exp_ts = expires if isinstance(expires, datetime) else None
                self.memoryd_client.save(
                    key=key,
                    value=value,
                    category=category,
                    tags=topics,
                    importance=float(importance),
                    expires_at=exp_ts,
                )
            except Exception:
                logger.debug("memoryd Spiegelung remember fehlgeschlagen", exc_info=True)
            topics_payload = list(topics) if topics else []
            importance_norm = max(0.1, min(1.0, float(importance) / 10.0))
            summary = condense_text(str(value), min_length=80, max_length=220)
            metadata = {
                'category': category,
                'source': source,
            }
            if topics_payload:
                metadata['topics'] = ','.join(str(topic) for topic in topics_payload)
            self.store_vector_memory(
                f"{category}:{key} -> {summary}",
                metadata=metadata,
                importance=importance_norm,
            )
            self.record_timeline_event(
                'long_term_memory',
                {
                    'action': 'remember',
                    'key': key,
                    'category': category,
                    'source': source,
                    'topics': topics_payload,
                },
                importance=importance_norm,
            )
        return success
    
    def recall(self, key: str, default: Any = None, update_access: bool = True) -> Any:
        """Ruft eine Information aus dem LangzeitgedÃ¤chtnis ab.
        
        Args:
            key: Der SchlÃ¼ssel der Information
            default: Standardwert, falls nicht gefunden
            update_access: Ob der Zugriffszeitpunkt aktualisiert werden soll
            
        Returns:
            Die gespeicherte Information oder der Standardwert
        """
        try:
            entry = self.memoryd_client.get(key)
            if entry and isinstance(entry, dict):
                return entry.get("value", default)
        except Exception:
            logger.debug("memoryd recall fallback auf lokal", exc_info=True)
        return self.long_term.recall(key, default, update_access)
        
    # --- Erweiterte Abfragemethoden ---
    
    def search_by_topic(self, topic: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Sucht nach Erinnerungen zu einem bestimmten Thema.
        
        Args:
            topic: Das gesuchte Thema
            limit: Maximale Anzahl von Ergebnissen
            
        Returns:
            Liste von passenden Erinnerungen, sortiert nach Relevanz
        """
        return self.long_term.search_by_topic(topic, limit)
    
    def get_recent_memories(self, days: int = 7, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Gibt kÃ¼rzlich erstellte oder genutzte Erinnerungen zurÃ¼ck.
        
        Args:
            days: Zeitraum in Tagen
            category: Optionale Kategorie zur Filterung
            
        Returns:
            Liste von Erinnerungen, sortiert nach letztem Zugriff
        """
        return self.long_term.get_recent_memories(days, category)
    
    def get_memories_by_date_range(self, start_date: datetime, end_date: datetime, 
                                 category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Gibt Erinnerungen in einem bestimmten Zeitraum zurÃ¼ck.
        
        Args:
            start_date: Anfangsdatum des Zeitraums
            end_date: Enddatum des Zeitraums
            category: Optionale Kategorie zur Filterung
            
        Returns:
            Liste von Erinnerungen im Zeitraum
        """
        return self.long_term.get_memories_by_date_range(start_date, end_date, category)
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Gibt Statistiken Ã¼ber das LangzeitgedÃ¤chtnis zurÃ¼ck.
        
        Returns:
            Dictionary mit verschiedenen Statistiken
        """
        return self.long_term.get_memory_stats()
    
    def _load_previous_topics(self) -> None:
        sessions_dir = self.data_dir / 'sessions'
        if not sessions_dir.exists():
            return
        candidate_file: Optional[Path] = None
        active_file = sessions_dir / 'session_active.json'
        if active_file.exists():
            candidate_file = active_file
        else:
            try:
                session_files = sorted(sessions_dir.glob('session_*.json'))
            except Exception:
                session_files = []
            if session_files:
                candidate_file = session_files[-1]
        if candidate_file is None:
            return
        try:
            payload = json.loads(candidate_file.read_text(encoding='utf-8'))
        except Exception as exc:
            logger.debug(f'Kontextthemen konnten nicht geladen werden: {exc}')
            return
        entries = payload.get('entries') or []
        for entry in entries:
            topics = entry.get('topics') or []
            for topic in topics:
                if topic:
                    self.active_topics.add(str(topic).lower())

    def get_active_topics(self) -> Set[str]:
        """Gibt die aktuell aktiven Themen zurÃ¼ck.
        
        Returns:
            Set von aktiven Themen
        """
        return self.active_topics.copy()
    
    def add_active_topic(self, topic: str) -> None:
        """FÃ¼gt ein Thema zu den aktiven Themen hinzu.
        
        Args:
            topic: Das hinzuzufÃ¼gende Thema
        """
        if topic:
            self.active_topics.add(topic.lower())
    
    def remove_active_topic(self, topic: str) -> None:
        """Entfernt ein Thema aus den aktiven Themen.
        
        Args:
            topic: Das zu entfernende Thema
        """
        self.active_topics.discard(topic.lower())
    
    def search_memories(self, query: str, category: Optional[str] = None, 
                       limit: int = 5) -> List[Dict[str, Any]]:
        """Durchsucht das LangzeitgedÃ¤chtnis nach relevanten Informationen.
        
        Args:
            query: Suchanfrage
            category: Optionale Kategorie zur EinschrÃ¤nkung der Suche
            limit: Maximale Anzahl von Ergebnissen
            
        Returns:
            Liste von passenden EintrÃ¤gen
        """
        try:
            results = self.memoryd_client.search(query, category=category, limit=limit)
            if results:
                return results
        except Exception:
            logger.debug("memoryd search fallback auf lokal", exc_info=True)
        return self.long_term.search(query, category, limit)
    
    # --- Kontextverwaltung ---
    
    def update_context(self, **kwargs) -> None:
        """Aktualisiert den aktuellen Kontext mit den angegebenen Werten."""
        self.current_context.update(kwargs)
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """Gibt einen Wert aus dem aktuellen Kontext zurÃ¼ck."""
        return self.current_context.get(key, default)
    
    def clear_context(self) -> None:
        """LÃ¶scht den aktuellen Kontext."""
        self.current_context = {}
    
    def _update_current_context(self, entry: Dict[str, Any]) -> None:
        """Aktualisiert den aktuellen Kontext basierend auf der letzten Nachricht."""
        # Basis-Kontext aktualisieren
        self.current_context.update({
            'last_role': entry['role'],
            'last_message': entry['content'],
            'timestamp': entry.get('timestamp', datetime.now().isoformat()),
            'topics': entry.get('topics', [])
        })
        
        # Aktive Themen aktualisieren, falls neue Themen in der Nachricht sind
        if 'topics' in entry and entry['topics']:
            self.active_topics.update(topic.lower() for topic in entry['topics'])
        
        # Spezielle Kontext-Aktualisierung fÃ¼r bestimmte Nachrichtentypen
        if entry['role'] == 'user':
            self._update_context_from_user_message(entry)
        else:  # assistant
            self._update_context_from_assistant_message(entry)
    
    def _update_context_from_user_message(self, entry: Dict[str, Any]) -> None:
        """Aktualisiert den Kontext basierend auf einer Benutzernachricht."""
        content = entry['content'].lower()
        
        # Erkenne spezielle Anfragen
        if any(word in content for word in ['erinnere', 'merke dir', 'nicht vergessen']):
            self.current_context['intent'] = 'remember_something'
        elif any(word in content for word in ['was haben wir besprochen', 'worÃ¼ber haben wir geredet']):
            self.current_context['intent'] = 'recall_conversation'
        elif 'thema' in content and ('wechsel' in content or 'Ã¤ndern' in content):
            self.current_context['intent'] = 'change_topic'
    
    def _update_context_from_assistant_message(self, entry: Dict[str, Any]) -> None:
        """Aktualisiert den Kontext basierend auf einer Assistenten-Nachricht."""
        # Hier kÃ¶nnen wir spezielle Kontext-Aktualisierungen fÃ¼r Assistenten-Nachrichten durchfÃ¼hren
        pass
    
    # --- Spezielle GedÃ¤chtnisfunktionen ---
    
    def remember_conversation_summary(self, summary: str, tags: List[str] = None) -> bool:
        """Speichert eine Zusammenfassung der aktuellen Konversation.
{{ ... }}
        Args:
            summary: Zusammenfassung der Konversation
            tags: Optionale Tags zur Kategorisierung
            
        Returns:
            True bei Erfolg, sonst False
        """
        if not summary.strip():
            return False
            
        # Erstelle einen eindeutigen SchlÃ¼ssel basierend auf dem aktuellen Datum
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        key = f"conversation_summary_{timestamp}"
        
        # Speichere die Zusammenfassung
        success = self.remember(
            key=key,
            value={
                'summary': summary,
                'timestamp': datetime.now().isoformat(),
                'tags': tags or [],
                'context': dict(self.current_context)
            },
            category="conversation_summaries"
        )
        
        if success:
            logger.info(f"Konversationszusammenfassung gespeichert: {key}")
        else:
            logger.error(f"Fehler beim Speichern der Konversationszusammenfassung: {key}")
            
        return success
    
    def get_recent_conversation_summaries(self, days: int = 7) -> List[Dict[str, Any]]:
        """Gibt die Zusammenfassungen der letzten Konversationen zurÃ¼ck.
        
        Args:
            days: Anzahl der Tage, die zurÃ¼ckgehen soll
            
        Returns:
            Liste von Konversationszusammenfassungen
        """
        # Hole alle Zusammenfassungen der letzten Tage
        all_summaries = self.long_term.search("conversation_summary", "conversation_summaries")
        
        # Filtere nach Datum
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_summaries = [
            s for s in all_summaries 
            if datetime.fromisoformat(s['timestamp']) > cutoff_date
        ]
        
        return recent_summaries
    
    def get_last_interaction_time(self) -> Optional[datetime]:
        """Gibt den Zeitpunkt der letzten Interaktion zurÃ¼ck."""
        if not self.conversation_history:
            return None
            
        last_msg = self.conversation_history[-1]
        timestamp = last_msg.get('timestamp')
        
        if isinstance(timestamp, str):
            return datetime.fromisoformat(timestamp)
        elif isinstance(timestamp, datetime):
            return timestamp
            
        return datetime.now()
