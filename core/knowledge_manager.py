# Knowledge management module for J.A.R.V.I.S.
# Handles local knowledge base and external API integrations.

import os
import sqlite3
import json
import requests
import hashlib
import re
import datetime
import uuid
import threading
from pathlib import Path
from typing import Any, Callable, Dict, Optional, List, Tuple

try:
    from sentence_transformers import CrossEncoder  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    CrossEncoder = None

try:
    import torch  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    torch = None

from utils.logger import Logger
from core.local_knowledge_scanner import LocalKnowledgeScanner
from core.local_knowledge_importer import LocalKnowledgeImporter
from core.memory_manager import MemoryManager
from config.persona import persona
from utils.text_shortener import condense_text


class KnowledgeManager:
    """Manages knowledge sources and caching."""

    def __init__(self) -> None:
        self.logger = Logger()
        self.creator_name = persona.creator_name or persona.user_name
        self.topic_aliases = {
            'jarvis creator': 'jarvis creator',
            'wer hat dich erschaffen': 'jarvis creator',
            'wer hat dich gebaut': 'jarvis creator',
            'wer hat dich gemacht': 'jarvis creator',
            'wer hat dich programmiert': 'jarvis creator',
            'wer ist dein entwickler': 'jarvis creator',
            'wer ist dein erschaffer': 'jarvis creator',
            'wer ist dein ersteller': 'jarvis creator',
            'wer hat dich erstellt': 'jarvis creator',
            'wer ist dein creator': 'jarvis creator',
            'wer ist dein erbauer': 'jarvis creator',
            'wer hat jarvis erschaffen': 'jarvis creator',
            'dein entwickler': 'jarvis creator',
            'dein erschaffer': 'jarvis creator'
        }
        self.db_path = Path("data/knowledge.db")
        self.cache_duration = 3600 * 24  # 24 hours
        self.api_cache_duration = 3600 * 12  # 12 hours

        self.wikipedia_plugin: Optional[Any] = None
        self.external_plugins: Dict[str, Any] = {}
        self.progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
        self.local_knowledge_scanner: Optional[LocalKnowledgeScanner] = None
        self.local_knowledge_dir: Optional[Path] = None
        self._local_scan_thread: Optional[threading.Thread] = None
        self.local_knowledge_importer: Optional[LocalKnowledgeImporter] = None
        self._local_import_thread: Optional[threading.Thread] = None
        self._auto_import_enabled: bool = True
        self._force_next_import: bool = False
        try:
            self.memory_manager = MemoryManager()
        except Exception as exc:
            self.logger.warning(f"MemoryManager konnte nicht initialisiert werden: {exc}")
            self.memory_manager = None

        self._cross_encoder_model = self._resolve_cross_encoder_model()
        self._cross_encoder = None
        self._cross_encoder_lock = threading.Lock()
        self._cross_encoder_disabled = False
        self._cross_encoder_device = "cpu"
        self._cross_encoder_batch_size = 8
        self._cross_encoder_fp16 = False

        self.setup_database()
        self.load_plugins()
        self._initialise_local_scanner()

        self.logger.info("Knowledge manager initialised")

    def _rewrite_result_heading(self, text: str, topic: str) -> str:
        try:
            import re as _re
            def repl(m):
                return f"{m.group(1)}{topic}{m.group(3)}"
            return _re.sub(r"(Wikipedia-Information zu ')([^']+)(':)", repl, text, count=1)
        except Exception:
            return text

    def _harmonize_wikipedia_message(self, text: str, topic: str) -> str:
        try:
            if not text or not isinstance(text, str):
                return text
            def _repl_heading(m):
                return f"{m.group(1)}{topic}{m.group(3)}"
            text = re.sub(r"(Wikipedia-Information zu ')([^']+)(':)", _repl_heading, text, count=1)
            def _repl_none(m):
                return f"{m.group(1)}{topic}{m.group(3)}"
            text = re.sub(r"(Keine Wikipedia-Artikel zu ')([^']+)(' gefunden\.)", _repl_none, text, count=1)
            def _repl_err(m):
                return f"{m.group(1)}{topic}{m.group(3)}"
            text = re.sub(r"(bei der Wikipedia-Suche zu ')([^']+)(' ist ein Fehler aufgetreten\.)", _repl_err, text, count=1)
            return text
        except Exception:
            return text

    def _canonicalize_topic(self, query: str) -> str:
        base = (query or "").strip().lower()
        if not base:
            return base
        for alias, canonical in self.topic_aliases.items():
            if alias in base:
                return canonical
        return base

    def _normalize_search_query(self, query: str) -> str:
        text = (query or '').strip()
        if not text:
            return text
        lower = text.lower()
        # Umlaute/? -> ASCII
        lower = lower.translate(str.maketrans({'?':'ae','?':'oe','?':'ue','?':'ss'}))
        fillers = [
            'suche nach ', 'suche ', 'finde ', 'infos ueber ', 'infos uber ', 'infos ',
            'information ueber ', 'informationen ueber ', 'information uber ', 'informationen uber ',
            'was ist ', 'wer ist ', 'zu ',
        ]
        stripped = True
        while stripped:
            stripped = False
            for f in fillers:
                if lower.startswith(f):
                    lower = lower[len(f):]
                    stripped = True
                    break
        if lower.startswith('ueber '):
            lower = lower[len('ueber '):]
        return ' '.join(lower.split())


    def _search_memory_layers(self, query: str, *, original_query: str = '', top_k: int = 3) -> Optional[str]:
        if not getattr(self, 'memory_manager', None) or not query:
            return None
        semantic_hits = self.memory_manager.search_vector_memory(query, top_k=top_k)
        timeline_hits = self.memory_manager.query_timeline(limit=5, search_text=query)
        if not semantic_hits and not timeline_hits:
            return None
        lines = ["=== Memory Layer (Vector + Timeline) ==="]
        if semantic_hits:
            lines.append("Semantische Treffer:")
            for hit in semantic_hits:
                snippet = condense_text(str(hit.get('text', '')), min_length=60, max_length=160)
                lines.append(f"- ({hit.get('score', 0.0):.2f}) {snippet}")
        if timeline_hits:
            if lines:
                lines.append('')
            lines.append("Zeitliche Ereignisse:")
            for event in timeline_hits:
                timestamp = str(event.get('timestamp', ''))[:19]
                event_type = event.get('event_type', 'event')
                payload = event.get('payload') or {}
                if isinstance(payload, dict):
                    content_value = payload.get('content') or payload.get('summary') or payload.get('description') or payload
                else:
                    content_value = payload
                snippet = condense_text(str(content_value), min_length=40, max_length=120)
                lines.append(f"- [{timestamp}] {event_type}: {snippet}")
        filtered = [line for line in lines if isinstance(line, str) and line.strip()]
        return '\n'.join(filtered)

    def _log_knowledge_observation(self, query: str, summary: Optional[str], *, source: str, importance: float = 0.5) -> None:
        if not getattr(self, 'memory_manager', None):
            return
        try:
            payload = {
                'query': query,
                'source': source,
                'has_result': bool(summary),
            }
            self.memory_manager.record_timeline_event('knowledge_lookup', payload, importance=importance)
            if summary:
                snippet = condense_text(summary, min_length=80, max_length=220)
                self.memory_manager.store_vector_memory(
                    f"{source}:{query} -> {snippet}",
                    metadata={'source': source, 'layer': 'knowledge'},
                    importance=importance,
                )
        except Exception:
            self.logger.debug('Knowledge memory logging failed', exc_info=True)

    def _resolve_cross_encoder_model(self) -> str:
        default = "cross-encoder/ms-marco-MiniLM-L6-v2"
        env_value = os.environ.get("JARVIS_CROSS_ENCODER_MODEL")
        if isinstance(env_value, str) and env_value.strip():
            return env_value.strip()
        settings_path = Path("data/settings.json")
        if settings_path.exists():
            try:
                data = json.loads(settings_path.read_text(encoding="utf-8"))
                candidate: Optional[str] = None
                if isinstance(data, dict):
                    retrieval_cfg = data.get("retrieval")
                    if isinstance(retrieval_cfg, dict):
                        candidate = retrieval_cfg.get("cross_encoder_model_name")
                    if not candidate:
                        candidate = data.get("cross_encoder_model_name")
                if candidate and isinstance(candidate, str) and candidate.strip():
                    return candidate.strip()
            except Exception as exc:
                self.logger.debug(f"Cross-Encoder Konfiguration konnte nicht gelesen werden: {exc}")
        return default

    def setup_database(self) -> None:
        """Create SQLite tables if needed."""
        try:
            self.db_path.parent.mkdir(exist_ok=True)

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT UNIQUE,
                    content TEXT,
                    source TEXT,
                    cached_at TIMESTAMP,
                    hash TEXT
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS search_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT UNIQUE,
                    results TEXT,
                    cached_at TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT,
                    response TEXT,
                    rating INTEGER,
                    feedback_text TEXT,
                    created_at TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT,
                    query TEXT,
                    result TEXT,
                    cached_at TIMESTAMP,
                    UNIQUE(source, query)
                )
            """)

            self._ensure_core_knowledge(cursor)

            conn.commit()
            conn.close()

            self.logger.info("Knowledge database initialised")

        except Exception as exc:
            self.logger.error(f"Database initialisation failed: {exc}")

    def _ensure_core_knowledge(self, cursor) -> None:
        try:
            topic = "jarvis creator"
            content = (
                f"J.A.R.V.I.S. wurde von {self.creator_name} entwickelt. "
                f"{self.creator_name} ist der Erbauer dieses Systems."
            )
            content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
            cursor.execute(
                """
                INSERT OR IGNORE INTO knowledge (topic, content, source, cached_at, hash)
                VALUES (?, ?, ?, ?, ?)
                """.strip(),
                (
                    topic,
                    content,
                    "System",
                    datetime.datetime.now(),
                    content_hash
                )
            )
        except Exception as exc:
            self.logger.error(f"Core knowledge seeding failed: {exc}")

    def load_plugins(self) -> None:
        """Import external knowledge plugins."""
        try:
            from plugins.wikipedia_plugin import WikipediaPlugin
            self.wikipedia_plugin = WikipediaPlugin()
            self.logger.info("Wikipedia plugin ready")
        except Exception as exc:
            self.wikipedia_plugin = None
            self.logger.error(f"Could not load Wikipedia plugin: {exc}")

        sources = {
            "openlibrary": "plugins.openlibrary_plugin.OpenLibraryPlugin",
            "openstreetmap": "plugins.openstreetmap_plugin.OpenStreetMapPlugin",
            "semanticscholar": "plugins.semantic_scholar_plugin.SemanticScholarPlugin",
            "pubmed": "plugins.pubmed_plugin.PubMedPlugin",
            "wikidata": "plugins.wikidata_plugin.WikidataPlugin",
        }
        self.external_plugins = {}
        for key, dotted_path in sources.items():
            module_name, class_name = dotted_path.rsplit('.', 1)
            try:
                module = __import__(module_name, fromlist=[class_name])
                cls = getattr(module, class_name)
                self.external_plugins[key] = cls()
                self.logger.info("Plugin geladen: %s", key)
            except Exception as exc:
                self.logger.error(f"Kann Plugin {key} nicht laden: {exc}")

    def register_progress_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Register a callback for long running operations."""
        self.progress_callback = callback

    def _report_progress(self, **payload: Any) -> None:
        if not self.progress_callback:
            return
        try:
            self.progress_callback(payload)
        except Exception as exc:
            self.logger.error(f"Progress callback failed: {exc}")

    def _initialise_local_scanner(self) -> None:
        try:
            self.local_knowledge_scanner = LocalKnowledgeScanner(
                project_root=Path.cwd(),
                logger=self.logger,
                progress_callback=self._handle_local_scan_progress
            )
            self.local_knowledge_dir = self.local_knowledge_scanner.output_dir
            self._initialise_local_importer()
            self._start_local_scan_thread()
        except Exception as exc:
            self.local_knowledge_scanner = None
            self.local_knowledge_dir = None
            self.logger.error(f"Local knowledge scanner initialisation failed: {exc}")

    def _initialise_local_importer(self) -> None:
        if not self.local_knowledge_dir:
            return
        try:
            self.local_knowledge_importer = LocalKnowledgeImporter(
                base_dir=self.local_knowledge_dir,
                cache_callback=self._cache_local_document,
                logger=self.logger,
                progress_callback=self._handle_local_import_progress
            )
            self._force_next_import = True
        except Exception as exc:
            self.local_knowledge_importer = None
            self.logger.error(f"Local knowledge importer initialisation failed: {exc}")

    def _cache_local_document(self, topic: str, content: str) -> None:
        try:
            self.cache_knowledge(topic, content, 'LocalWissen')
        except Exception as exc:
            self.logger.error(f"Caching local knowledge failed for {topic}: {exc}")

    def _start_local_scan_thread(self) -> None:
        if not self.local_knowledge_scanner:
            return
        worker = threading.Thread(
            target=self.local_knowledge_scanner.scan,
            name='LocalKnowledgeScan',
            daemon=True
        )
        self._local_scan_thread = worker
        worker.start()

    def _start_local_import_thread(self, *, force: bool = False) -> None:
        if not self.local_knowledge_importer:
            return
        force_run = force or self._force_next_import
        if force_run:
            self._force_next_import = False

        def _runner() -> None:
            try:
                self.local_knowledge_importer.import_local_knowledge(force=force_run)
            except Exception as exc:
                self.logger.error(f"Local knowledge import failed: {exc}")

        worker = threading.Thread(
            target=_runner,
            name='LocalKnowledgeImport',
            daemon=True
        )
        self._local_import_thread = worker
        worker.start()

    def _handle_local_scan_progress(self, payload: Dict[str, Any]) -> None:
        data = dict(payload or {})
        data.setdefault('source', 'local_knowledge')
        stage = data.get('stage')
        if 'message' not in data and stage:
            if stage == 'local_scan_start':
                data['message'] = 'Lokaler Wissensscan gestartet'
            elif stage == 'local_scan_complete':
                copied = data.get('copied', 0)
                skipped = data.get('skipped', 0)
                data['message'] = f"Lokaler Wissensscan abgeschlossen (kopiert: {copied}, uebersprungen: {skipped})"
            else:
                data['message'] = f"Lokaler Wissensscan: {stage}"
        self._report_progress(**data)
        if stage == 'local_scan_complete' and self._auto_import_enabled:
            self._start_local_import_thread()

    def _handle_local_import_progress(self, payload: Dict[str, Any]) -> None:
        data = dict(payload or {})
        data.setdefault('source', 'local_knowledge')
        stage = data.get('stage')
        if stage == 'local_import_start':
            total = data.get('total', 0)
            data['message'] = f"Importiere lokales Wissen ({total} Dateien)"
        elif stage == 'local_import_file':
            index = data.get('index', 0)
            total = data.get('total', 0)
            file_name = data.get('file')
            if total:
                data['message'] = f"Importiere {index}/{total}: {file_name}"
            else:
                data['message'] = f"Importiere {file_name}"
        elif stage == 'local_import_complete':
            processed = data.get('processed', 0)
            unchanged = data.get('unchanged', 0)
            data['message'] = f"Lokales Wissen aktualisiert (neu: {processed}, unveraendert: {unchanged})"
        self._report_progress(**data)

    def refresh_local_knowledge(self, blocking: bool = False) -> bool:
        if not self.local_knowledge_scanner:
            return False
        if blocking:
            previous_auto_state = self._auto_import_enabled
            self._auto_import_enabled = False
            try:
                self.local_knowledge_scanner.scan()
            finally:
                self._auto_import_enabled = previous_auto_state
            if self.local_knowledge_importer:
                force_flag = self._force_next_import or False
                self._force_next_import = False
                self.local_knowledge_importer.import_local_knowledge(force=force_flag)
            return True
        self._start_local_scan_thread()
        return True

    def get_local_knowledge_path(self) -> Optional[Path]:
        if self.local_knowledge_scanner:
            return self.local_knowledge_scanner.output_dir
        return None

    def search_knowledge(self, query: str) -> Optional[str]:
        """Search knowledge across memory, local cache and external sources."""
        if not query or not query.strip():
            return None

        normalized = self._normalize_search_query(query)
        search_key = normalized or (query or "").strip().lower()
        search_key = self._canonicalize_topic(search_key)

        aggregated_parts: List[str] = []

        memory_layer = self._search_memory_layers(search_key, original_query=query)
        if memory_layer:
            aggregated_parts.append(memory_layer)
            self._log_knowledge_observation(search_key, memory_layer, source="memory", importance=0.3)

        local_result = self.search_local_knowledge(search_key)
        if local_result:
            aggregated_parts.append(local_result)
            self._log_knowledge_observation(search_key, local_result, source="local", importance=0.6)
        else:
            external_result = self.search_external_sources(search_key)
            if external_result:
                self.cache_knowledge(search_key, external_result)
                aggregated_parts.append(external_result)
                self._log_knowledge_observation(search_key, external_result, source="external", importance=0.7)
            else:
                self._log_knowledge_observation(search_key, None, source="external", importance=0.2)

        combined = "\n\n".join(part.strip() for part in aggregated_parts if isinstance(part, str) and part.strip())
        return combined or None

    def search_local_knowledge(self, query: str) -> Optional[str]:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT content, source, topic, cached_at
                FROM knowledge
                WHERE cached_at > ?
                  AND (topic LIKE ? OR content LIKE ?)
                ORDER BY cached_at DESC
                LIMIT 8
                """,
                (
                    datetime.datetime.now() - datetime.timedelta(seconds=self.cache_duration),
                    f"%{query}%",
                    f"%{query}%",
                )
            )
            rows = cursor.fetchall()
            conn.close()
            if not rows:
                return None

            best = self._select_best_local_match(query, rows)
            if best:
                content, source, _topic, _cached_at, score, probability = best
                if score is not None:
                    if probability is not None:
                        self.logger.debug(
                            "Cross-Encoder Score %.3f (p=%.3f) fuer Quelle %s",
                            float(score),
                            float(probability),
                            source,
                        )
                    else:
                        self.logger.debug("Cross-Encoder Score %.3f fuer Quelle %s", float(score), source)
                return f"{content}\n\nQuelle: {source}"
            return None
        except Exception as exc:
            self.logger.error(f"Local search failed: {exc}")
            return None

    def _select_best_local_match(
        self,
        query: str,
        rows: List[Tuple[str, str, str, str]],
    ) -> Optional[Tuple[str, str, str, str, Optional[float], Optional[float]]]:
        if not rows:
            return None
        try:
            prepared_entries: List[Tuple[str, str, str, str, str]] = []
            snippets: List[str] = []
            for content, source, topic, cached_at in rows:
                snippet = self._prepare_passage_for_rerank(content)
                if not snippet:
                    continue
                prepared_entries.append((content, source, topic, cached_at, snippet))
                snippets.append(snippet)
            if not prepared_entries:
                return None

            rank_result = self._compute_cross_encoder_scores(query, snippets)
            if rank_result is None:
                content, source, topic, cached_at, _ = prepared_entries[0]
                return (content, source, topic, cached_at, None, None)

            scores, probabilities = rank_result
            scored = list(zip(prepared_entries, scores, probabilities))
            scored.sort(key=lambda item: float(item[1]), reverse=True)
            best_entry, best_score, best_prob = scored[0]
            content, source, topic, cached_at, _snippet = best_entry
            return (content, source, topic, cached_at, float(best_score), float(best_prob) if best_prob is not None else None)
        except Exception as exc:
            self.logger.warning(f"Cross-Encoder Bewertung fehlgeschlagen: {exc}")
            content, source, topic, cached_at = rows[0]
            return (content, source, topic, cached_at, None, None)

    def _prepare_passage_for_rerank(self, passage: str, *, max_chars: int = 960) -> str:
        text = (passage or "").strip()
        if not text:
            return ""
        if len(text) <= max_chars:
            return text
        sentences = re.split(r"(?<=[\.!?])\s+", text)
        truncated: List[str] = []
        total = 0
        for sentence in sentences:
            cleaned = sentence.strip()
            if not cleaned:
                continue
            sentence_len = len(cleaned) + 1
            if total + sentence_len > max_chars:
                break
            truncated.append(cleaned)
            total += sentence_len
        if truncated:
            return " ".join(truncated)
        return text[:max_chars]

    def _compute_cross_encoder_scores(
        self,
        query: str,
        passages: List[str],
    ) -> Optional[Tuple[List[float], List[Optional[float]]]]:
        encoder = self._ensure_cross_encoder()
        if encoder is None or torch is None:
            return None
        model = getattr(encoder, "model", None)
        tokenizer = getattr(encoder, "tokenizer", None)
        if model is None or tokenizer is None:
            return None
        device = torch.device(self._cross_encoder_device or "cpu")
        batch_size = self._cross_encoder_batch_size or 8
        max_length = getattr(encoder, "max_length", 512) or 512
        scores: List[float] = []
        probabilities: List[Optional[float]] = []
        model.eval()

        try:
            for start in range(0, len(passages), batch_size):
                chunk = passages[start : start + batch_size]
                queries = [query] * len(chunk)
                try:
                    tokenized = tokenizer(
                        queries,
                        chunk,
                        padding=True,
                        truncation="only_second",
                        max_length=max_length,
                        return_tensors="pt",
                    )
                except Exception:
                    tokenized = tokenizer(
                        queries,
                        chunk,
                        padding=True,
                        truncation="longest_first",
                        max_length=max_length,
                        return_tensors="pt",
                    )
                tokenized = {key: value.to(device) for key, value in tokenized.items()}
                with torch.no_grad():
                    if self._cross_encoder_fp16 and device.type == "cuda":
                        with torch.cuda.amp.autocast(dtype=torch.float16):
                            logits = model(**tokenized).logits
                    else:
                        logits = model(**tokenized).logits
                logits = logits.squeeze(-1).detach().cpu()
                scores.extend(logits.tolist())
                if torch is not None:
                    prob = torch.sigmoid(logits)
                    probabilities.extend(prob.tolist())
                else:
                    probabilities.extend([None] * len(chunk))
        except Exception as exc:
            self.logger.warning(f"Cross-Encoder Inferenz fehlgeschlagen: {exc}")
            self._cross_encoder_disabled = True
            return None

        return scores, probabilities

    def _ensure_cross_encoder(self):
        if self._cross_encoder_disabled:
            return None
        if CrossEncoder is None or torch is None:
            if not self._cross_encoder_disabled:
                self.logger.info(
                    "Cross-Encoder nicht verfuegbar. Bitte 'pip install sentence-transformers torch' installieren."
                )
            self._cross_encoder_disabled = True
            return None
        if self._cross_encoder is not None:
            return self._cross_encoder
        with self._cross_encoder_lock:
            if self._cross_encoder is not None:
                return self._cross_encoder
            try:
                device = "cuda" if torch.cuda.is_available() else "cpu"
                encoder = CrossEncoder(self._cross_encoder_model, device=device, max_length=512)
                encoder.model.eval()
                if device == "cuda":
                    try:
                        encoder.model.half()
                        self._cross_encoder_fp16 = True
                    except Exception:
                        self._cross_encoder_fp16 = False
                else:
                    self._cross_encoder_fp16 = False
                self._cross_encoder = encoder
                self._cross_encoder_device = device
                self._cross_encoder_batch_size = 32 if device == "cuda" else 8
                self.logger.info("Cross-Encoder (%s) geladen (device=%s).", self._cross_encoder_model, device)
            except Exception as exc:
                self._cross_encoder_disabled = True
                self._cross_encoder = None
                self.logger.warning(
                    "Cross-Encoder konnte nicht geladen werden (%s). Installiere mit 'pip install sentence-transformers torch'.",
                    exc,
                )
            return self._cross_encoder

    def search_external_sources(self, query: str) -> Optional[str]:
        norm = self._normalize_search_query(query)
        canon = self._canonicalize_topic(norm or query)
        norm = canon or norm
        sources = []
        if self.wikipedia_plugin:
            sources.append(("wikipedia", self.wikipedia_plugin))
        for key in ("openlibrary", "semanticscholar", "openstreetmap"):
            plugin = self.external_plugins.get(key)
            if plugin:
                sources.append((key, plugin))

        for source_key, plugin in sources:
            cached = self._get_cached_api_result(source_key, norm)
            if cached:
                self.logger.debug("API cache hit for %s", source_key)
                return cached
            try:
                result = plugin.search(norm)
                if result:
                    result = self._harmonize_wikipedia_message(result, norm)
                    result = self._rewrite_result_heading(result, norm)
                    # Nur erfolgreiche Inhalte cachen, nicht die 'Keine Artikel'-Hinweise
                    if not result.startswith("Keine Wikipedia-Artikel"):
                        self._store_api_result(source_key, norm, result)
                    return result
            except Exception as exc:
                self.logger.error(f"External search failed via {source_key}: {exc}")
        return None

    def search_external_sources_async(self, query: str) -> Optional[str]:
        return self.search_external_sources(query)

    def neural_synthesis(self, query: str, *, max_sources: int = 4) -> Optional[Dict[str, Any]]:
        """Kombiniert Wissen aus mehreren Quellen zu einer verdichteten Antwort."""
        if not query or not query.strip():
            return None
        normalized = self._normalize_search_query(query)
        canonical = self._canonicalize_topic(normalized or query)
        search_key = canonical or normalized or query

        sources: List[Dict[str, Any]] = []

        local_entries = self._collect_local_entries(search_key, limit=max_sources)
        sources.extend(local_entries)

        external_limit = max(0, max_sources - len(sources))
        if external_limit:
            external_entries = self._collect_external_entries(search_key, limit=external_limit)
            sources.extend(external_entries)

        if not sources:
            return None

        combined_text = "\n\n".join(entry.get("content", "") for entry in sources if entry.get("content"))
        summary = combined_text.strip()
        if summary:
            try:
                summary = condense_text(summary, min_length=220, max_length=720)
            except Exception:
                summary = summary[:720] + "…" if len(summary) > 721 else summary

        return {
            "query": search_key,
            "summary": summary,
            "sources": sources,
            "source_count": len(sources),
        }

    def _collect_local_entries(self, query: str, *, limit: int = 2) -> List[Dict[str, Any]]:
        """Sammelt passende Einträge aus der lokalen Wissensbasis."""
        entries: List[Dict[str, Any]] = []
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT topic, content, source, cached_at
                FROM knowledge
                WHERE topic LIKE ?
                  AND cached_at > ?
                ORDER BY CASE WHEN LOWER(topic) = LOWER(?) THEN 0 ELSE 1 END,
                         LENGTH(topic) ASC
                LIMIT ?
                """,
                (
                    f"%{query}%",
                    datetime.datetime.now() - datetime.timedelta(seconds=self.cache_duration),
                    query,
                    limit,
                ),
            )
            rows = cursor.fetchall()
            conn.close()
        except Exception as exc:
            self.logger.error(f"Lokale Neural-Sammlung fehlgeschlagen: {exc}")
            rows = []

        for topic, content, source, cached_at in rows:
            text = content or ""
            highlight = text
            if text:
                try:
                    highlight = condense_text(text, min_length=120, max_length=260)
                except Exception:
                    highlight = text[:260] + "…" if len(text) > 261 else text
            entries.append({
                "origin": "local",
                "topic": topic,
                "source": source or "Lokale Wissensbasis",
                "cached_at": cached_at,
                "content": text,
                "highlight": highlight.strip(),
                "label": f"Lokale Quelle: {topic}",
            })
        return entries

    def _collect_external_entries(self, query: str, *, limit: int = 2) -> List[Dict[str, Any]]:
        """Fragt externe Quellen sequenziell ab und sammelt Ergebnisse."""
        entries: List[Dict[str, Any]] = []
        norm_query = self._normalize_search_query(query)
        canonical = self._canonicalize_topic(norm_query or query)
        search_key = canonical or norm_query or query

        sources: List[Tuple[str, Any, str]] = []
        if self.wikipedia_plugin:
            sources.append(("wikipedia", self.wikipedia_plugin, "Wikipedia"))
        for key, label in (("openlibrary", "OpenLibrary"), ("semanticscholar", "SemanticScholar"), ("openstreetmap", "OpenStreetMap")):
            plugin = self.external_plugins.get(key)
            if plugin:
                sources.append((key, plugin, label))

        for source_key, plugin, display_name in sources:
            if len(entries) >= limit:
                break
            cached = self._get_cached_api_result(source_key, search_key)
            result_text = cached
            cached_flag = bool(cached)

            if not result_text:
                try:
                    result_text = plugin.search(search_key)
                    if result_text:
                        result_text = self._harmonize_wikipedia_message(result_text, search_key)
                        result_text = self._rewrite_result_heading(result_text, search_key)
                        if not str(result_text).startswith("Keine Wikipedia-Artikel"):
                            self._store_api_result(source_key, search_key, result_text)
                except Exception as exc:
                    self.logger.error(f"Neural Mode: Quelle {source_key} fehlgeschlagen: {exc}")
                    continue

            if not result_text:
                continue

            highlight = result_text
            try:
                highlight = condense_text(str(result_text), min_length=120, max_length=260)
            except Exception:
                text = str(result_text)
                highlight = text[:260] + "…" if len(text) > 261 else text

            entries.append({
                "origin": "external",
                "source_key": source_key,
                "source": display_name,
                "cached": cached_flag,
                "content": str(result_text),
                "highlight": str(highlight).strip(),
                "label": f"Externe Quelle: {display_name}",
            })

        return entries

    def cache_knowledge(self, topic: str, content: str, source: str = "Extern") -> None:
        topic = self._canonicalize_topic(topic)
        if not topic:
            return
        if not content:
            return
        lowered = content.strip().lower()
        if lowered.startswith("keine wikipedia-artikel") or lowered.startswith("entschuldigung, bei der wikipedia-suche") or lowered.startswith("keine detaillierten informationen"):
            self.logger.debug("Skip knowledge cache for %s due to empty result", topic)
            return
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
            cursor.execute(
                """
                INSERT OR REPLACE INTO knowledge (topic, content, source, cached_at, hash)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    topic,
                    content,
                    source,
                    datetime.datetime.now(),
                    content_hash,
                )
            )
            conn.commit()
            conn.close()
            self.logger.info("Knowledge cached for topic: %s", topic)
        except Exception as exc:
            self.logger.error(f"Knowledge cache failed: {exc}")

    def add_entry(self, *, source: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[int]:
        """Persist a knowledge entry and mirror it into the memory layers."""
        if not content:
            return None
        payload = metadata.copy() if isinstance(metadata, dict) else {}
        topic_hint = payload.get("topic") or payload.get("title") or payload.get("url") or source
        canonical = self._canonicalize_topic(topic_hint) if isinstance(topic_hint, str) else source
        doc_id = payload.get("document_id")
        unique_topic = f"{canonical}:{doc_id}" if doc_id else f"{canonical}:{uuid.uuid4().hex[:8]}"
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
            cursor.execute(
                """
                INSERT OR REPLACE INTO knowledge (topic, content, source, cached_at, hash)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    unique_topic,
                    content,
                    source,
                    datetime.datetime.now(),
                    content_hash,
                )
            )
            conn.commit()
            conn.close()
            if getattr(self, "memory_manager", None):
                try:
                    snippet = condense_text(content, min_length=120, max_length=400)
                    self.memory_manager.store_vector_memory(
                        snippet,
                        metadata={
                            "source": source,
                            **{k: str(v) for k, v in payload.items() if v is not None},
                        },
                        importance=float(payload.get("importance", 0.4) or 0.4),
                    )
                except Exception:
                    self.logger.debug("Vector memory ingestion failed for crawler document", exc_info=True)
            return cursor.lastrowid
        except Exception as exc:
            self.logger.error(f"Knowledge entry could not be written: {exc}")
            return None

    def import_crawler_documents(self, documents: List[Dict[str, Any]]) -> int:
        """Import crawled documents into the Jarvis knowledge base."""
        if not documents:
            return 0
        imported = 0
        for doc in documents:
            text = doc.get("text")
            if not isinstance(text, str) or not text.strip():
                continue
            metadata = {
                "document_id": doc.get("id"),
                "url": doc.get("url"),
                "title": doc.get("title"),
                "lang": doc.get("lang"),
                "domain": doc.get("domain"),
                "job_id": doc.get("job_id"),
                "crawl_topic": doc.get("crawl_topic"),
                "created_at": doc.get("created_at"),
                "topic": doc.get("crawl_topic") or doc.get("title"),
            }
            entry_id = self.add_entry(source="web_crawler", content=text, metadata=metadata)
            if entry_id:
                imported += 1
        return imported

    def count_entries_by_source(self, source: str) -> int:
        """Return the number of cached knowledge entries for a given source identifier."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM knowledge WHERE source = ?", (source,))
            result = cursor.fetchone()
            conn.close()
            if not result:
                return 0
            return int(result[0])
        except Exception as exc:
            self.logger.error(f"Source stats failed: {exc}")
            return 0

    def count_entries_by_source_since(self, source: str, since: datetime.datetime) -> int:
        """Return number of entries written since timestamp."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM knowledge WHERE source = ? AND datetime(cached_at) >= datetime(?)",
                (source, since.isoformat()),
            )
            result = cursor.fetchone()
            conn.close()
            if not result:
                return 0
            return int(result[0])
        except Exception as exc:
            self.logger.error(f"Source stats (since) failed: {exc}")
            return 0

    def fetch_entries_by_source(
        self,
        source: str,
        *,
        limit: int = 50,
        since: Optional[datetime.datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Return a list of knowledge entries for UI display."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            query = "SELECT id, topic, content, cached_at FROM knowledge WHERE source = ?"
            params: List[Any] = [source]
            if since:
                query += " AND datetime(cached_at) >= datetime(?)"
                params.append(since.isoformat())
            query += " ORDER BY datetime(cached_at) DESC LIMIT ?"
            params.append(int(limit))
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            entries: List[Dict[str, Any]] = []
            for row in rows:
                entries.append(
                    {
                        "id": row[0],
                        "topic": row[1],
                        "content": row[2],
                        "cached_at": row[3],
                    }
                )
            return entries
        except Exception as exc:
            self.logger.error(f"Source fetch failed: {exc}")
            return []

    def _get_cached_api_result(self, source: str, query: str) -> Optional[str]:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT result, cached_at FROM api_cache WHERE source = ? AND query = ?",
                (source, query)
            )
            row = cursor.fetchone()
            conn.close()
            if not row:
                return None
            result, cached_at = row
            cached_time = datetime.datetime.fromisoformat(cached_at)
            if datetime.datetime.now() - cached_time > datetime.timedelta(seconds=self.api_cache_duration):
                self._purge_api_entry(source, query)
                return None
            return result
        except Exception as exc:
            self.logger.error(f"API cache read failed: {exc}")
            return None

    def _store_api_result(self, source: str, query: str, result: Any) -> None:
        payload = result if isinstance(result, str) else json.dumps(result, ensure_ascii=False)
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO api_cache (source, query, result, cached_at) VALUES (?, ?, ?, ?)",
                (source, query, payload, datetime.datetime.now().isoformat())
            )
            conn.commit()
            conn.close()
        except Exception as exc:
            self.logger.error(f"API cache write failed: {exc}")

    def _purge_api_entry(self, source: str, query: str) -> None:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM api_cache WHERE source = ? AND query = ?", (source, query))
            conn.commit()
            conn.close()
        except Exception:
            pass

    def collect_knowledge_about_topic(self, topic: str) -> Optional[str]:
        """Aggregate knowledge from multiple providers."""
        canonical_topic = self._canonicalize_topic(topic)
        topic = canonical_topic or topic
        self.logger.info("Collecting knowledge about: %s", topic)
        self._report_progress(stage="start", topic=topic)

        knowledge_parts = []
        sources = [
            ("Wikipedia", self.wikipedia_plugin),
            ("OpenLibrary", self.external_plugins.get("openlibrary")),
            ("SemanticScholar", self.external_plugins.get("semanticscholar")),
            ("PubMed", self.external_plugins.get("pubmed")),
            ("Wikidata", self.external_plugins.get("wikidata")),
        ]
        active_sources = [entry for entry in sources if entry[1]]
        for index, (source_name, plugin) in enumerate(active_sources, 1):
            self._report_progress(stage="fetch", topic=topic, source=source_name, index=index, total=len(active_sources))
            if not plugin:
                continue
            try:
                result = plugin.search(topic)
                if result:
                    knowledge_parts.append({
                        'source': source_name,
                        'content': result,
                        'type': 'article',
                    })
            except Exception as exc:
                self.logger.error(f"Collection failed for {source_name}: {exc}")

        if knowledge_parts:
            combined = self.combine_knowledge_sources(topic, knowledge_parts)
            self.cache_knowledge(topic, combined, "Automatic collection")
            self._report_progress(stage="complete", topic=topic, success=True)
            return combined

        self._report_progress(stage="complete", topic=topic, success=False)
        return None

    def combine_knowledge_sources(self, topic, knowledge_parts):
        """Join multiple knowledge fragments."""
        combined = f"=== Wissen ueber {topic} ===\n\n"
        for index, part in enumerate(knowledge_parts, 1):
            combined += f"## Quelle {index}: {part['source']}\n"
            combined += f"{part['content']}\n\n"
            combined += "---\n\n"
        combined += f"Zusammengestellt am: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}"
        return combined

    def add_user_feedback(self, query, response, rating, feedback_text=""):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO feedback (query, response, rating, feedback_text, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    query,
                    response,
                    rating,
                    feedback_text,
                    datetime.datetime.now()
                )
            )
            conn.commit()
            conn.close()
            self.logger.info(f"Feedback gespeichert: Query={query}, Rating={rating}")
        except Exception as e:
            self.logger.error(f"Fehler beim Speichern des Feedbacks: {e}")

    def get_knowledge_stats(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM knowledge")
            total_articles = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM search_cache")
            cached_searches = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM feedback")
            feedback_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM api_cache")
            api_cache_entries = cursor.fetchone()[0]
            conn.close()
            return {
                'articles': total_articles,
                'cached_searches': cached_searches,
                'feedback_entries': feedback_count,
                'api_cache_entries': api_cache_entries,
            }
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen der Statistiken: {e}")
            return {
                'articles': 0,
                'cached_searches': 0,
                'feedback_entries': 0,
                'api_cache_entries': 0,
            }

    def cleanup_old_cache(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cutoff_date = datetime.datetime.now() - datetime.timedelta(seconds=self.cache_duration * 7)
            api_cutoff = datetime.datetime.now() - datetime.timedelta(seconds=self.api_cache_duration)
            cursor.execute("DELETE FROM knowledge WHERE cached_at < ?", (cutoff_date,))
            cursor.execute("DELETE FROM search_cache WHERE cached_at < ?", (cutoff_date,))
            cursor.execute("DELETE FROM api_cache WHERE cached_at < ?", (api_cutoff.isoformat(),))
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            self.logger.info(f"Cache bereinigt: {deleted_count} Datensaetze entfernt")
        except Exception as e:
            self.logger.error(f"Fehler bei Cache-Bereinigung: {e}")







