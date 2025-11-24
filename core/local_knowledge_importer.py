"""Local knowledge importer for converting LocalWissen files into the knowledge cache."""

import csv
import hashlib
import json
import threading
from fnmatch import fnmatch
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Optional, Set, Tuple

from utils.logger import Logger


class LocalKnowledgeImporter:
    """Reads mirrored LocalWissen files and stores their content in the knowledge cache."""

    TEXT_EXTENSIONS = {
        ".txt",
        ".md",
        ".rtf",
        ".log",
        ".ini",
        ".cfg",
        ".csv",
        ".json",
        ".xml",
        ".yaml",
        ".yml",
        ".html",
        ".htm"
    }

    SKIP_FILENAMES = {
        "manifest.json",
        "import_manifest.json",
        "desktop.ini",
        "config.json",
        "knowledge_base.json",
        "vector_memory.json",
    }

    SKIP_PARTS = {
        '__pycache__',
        '.venv',
        'venv',
        'env',
        'site-packages',
        'node_modules',
        '.git',
        '.safe',
    }

    MAX_CONTENT_CHARS = 20000
    INDEX_FILENAME = "import_manifest.json"

    def __init__(
        self,
        base_dir: Path,
        cache_callback: Callable[[str, str], None],
        *,
        logger: Optional[Logger] = None,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        allowed_extensions: Optional[Iterable[str]] = None
    ) -> None:
        self.base_dir = Path(base_dir)
        self.cache_callback = cache_callback
        self.logger = logger or Logger()
        self.progress_callback = progress_callback

        merged_exts = set(self.TEXT_EXTENSIONS)
        if allowed_extensions:
            merged_exts.update(ext.lower() if ext.startswith('.') else f".{ext.lower()}" for ext in allowed_extensions)
        self.allowed_extensions = {ext for ext in merged_exts}

        self.index_path = self.base_dir / self.INDEX_FILENAME
        self._index_files: Dict[str, Dict[str, Any]] = {}
        self._index_meta: Dict[str, Any] = self._default_meta()
        self._blacklist_exact: Set[str] = set()
        self._blacklist_patterns: Tuple[str, ...] = tuple()
        self._lock = threading.Lock()
        self._is_running = False
        self._load_index()

    def import_local_knowledge(self, force: bool = False) -> Dict[str, int]:
        """Import files into the knowledge cache."""
        if not self._acquire_lock():
            self.logger.debug("Local knowledge import already running")
            return {}
        try:
            if not self.base_dir.exists():
                self.logger.warning("LocalWissen-Verzeichnis nicht gefunden: %s", self.base_dir)
                return {}

            candidates = [path for path in self.base_dir.rglob('*') if path.is_file() and self._is_supported(path)]
            total = len(candidates)
            stats = {
                'processed': 0,
                'skipped': 0,
                'unchanged': 0,
                'errors': 0
            }

            self._notify('local_import_start', total=total)
            updated_index: Dict[str, Dict[str, Any]] = {}

            for index, path in enumerate(candidates, 1):
                relative_key = path.relative_to(self.base_dir).as_posix()
                try:
                    self.logger.debug("Importiere Datei (%s/%s): %s", index, total, relative_key)
                    metadata = self._index_files.get(relative_key)
                    if not force and metadata and not self._needs_update(path, metadata):
                        stats['unchanged'] += 1
                        updated_index[relative_key] = metadata
                        continue

                    text_content = self._extract_text(path)
                    if not text_content:
                        stats['skipped'] += 1
                        continue

                    header = self._build_header(path)
                    payload = f"{header}\n\n{text_content}"[:self.MAX_CONTENT_CHARS]
                    payload_hash = hashlib.sha1(payload.encode('utf-8', errors='ignore')).hexdigest()

                    topic = f"localwissen::{relative_key.lower()}"
                    self.cache_callback(topic, payload)

                    updated_index[relative_key] = {
                        'mtime': path.stat().st_mtime,
                        'size': path.stat().st_size,
                        'hash': payload_hash,
                        'cached': True
                    }
                    stats['processed'] += 1
                    self._notify('local_import_file', index=index, total=total, file=relative_key)
                except Exception as exc:
                    stats['errors'] += 1
                    self.logger.error("Fehler beim Import von %s: %s", path, exc)

            self._index_files = updated_index
            self._save_index()
            self._notify('local_import_complete', **stats)
            return stats
        finally:
            self._release_lock()

    # Internal helpers -------------------------------------------------

    def _acquire_lock(self) -> bool:
        if not self._lock.acquire(blocking=False):
            return False
        if self._is_running:
            self._lock.release()
            return False
        self._is_running = True
        self._lock.release()
        return True

    def _release_lock(self) -> None:
        with self._lock:
            self._is_running = False

    def _is_supported(self, path: Path) -> bool:
        suffix = path.suffix.lower()
        if suffix == '' and path.name.lower().endswith('.log'):  # handle double suffix like .1.log
            suffix = '.log'
        if path.name.lower() in self.SKIP_FILENAMES:
            return False
        try:
            relative_parts = [part.lower() for part in path.relative_to(self.base_dir).parts]
            if any(part in self.SKIP_PARTS for part in relative_parts):
                return False
            relative_key = '/'.join(relative_parts)
            if self._is_blacklisted(relative_key):
                return False
        except Exception:
            try:
                rel_key = path.relative_to(self.base_dir).as_posix().lower()
                if self._is_blacklisted(rel_key):
                    return False
            except Exception:
                pass
        return suffix in self.allowed_extensions and not path.name.startswith('.~lock')

    def _needs_update(self, path: Path, metadata: Dict[str, Any]) -> bool:
        try:
            stat = path.stat()
        except OSError:
            return True
        if metadata.get('cached') is not True:
            return True
        if stat.st_mtime != metadata.get('mtime') or stat.st_size != metadata.get('size'):
            return True
        payload_hash = metadata.get('hash')
        if not payload_hash:
            return True
        return False

    def _extract_text(self, path: Path) -> Optional[str]:
        suffix = path.suffix.lower()
        try:
            # Leere Dateien direkt ueberspringen
            try:
                if path.stat().st_size == 0:
                    return ''
            except Exception:
                pass
            if suffix in {'.txt', '.md', '.rtf', '.log', '.ini', '.cfg'}:
                return self._read_plain_text(path)
            if suffix in {'.json', '.yaml', '.yml', '.xml'}:
                return self._read_structured_text(path)
            if suffix == '.csv':
                return self._read_csv(path)
            if suffix in {'.html', '.htm'}:
                return self._strip_html(path)
        except Exception as exc:
            self.logger.error("Fehler beim Lesen von %s: %s", path, exc)
            return None
        return None

    def _read_plain_text(self, path: Path) -> str:
        try:
            # Robustes Lesen: erst Bytes laden, dann mehrere Encodings testen
            raw = path.read_bytes()
            # Binär-Schnellerkennung: NUL-Bytes -> nicht als Text behandeln
            if b"\x00" in raw[:1024]:
                self.logger.debug("Binärinhalt erkannt, Textlese übersprungen: %s", path)
                return ''
            # Bevorzugte Reihenfolge inkl. BOM/UTF-16 Varianten
            try_encodings = [
                'utf-8',
                'utf-8-sig',
                'utf-16',
                'utf-16-le',
                'utf-16-be',
                'cp1252',
                'latin-1',
            ]
            for enc in try_encodings:
                try:
                    text = raw.decode(enc)
                    self.logger.debug("Plain-Text erfolgreich decodiert mit %s: %s", enc, path)
                    return text
                except UnicodeDecodeError:
                    continue
                except Exception:
                    # defensive: unbekannte Fehler bei einzelnen Encodings ignorieren
                    continue
            # Letzter Fallback: UTF-8 mit Ignorieren fehlerhafter Bytes
            self.logger.debug("Plain-Text Fallback (utf-8, ignore errors): %s", path)
            return raw.decode('utf-8', errors='ignore')
        except Exception as exc:
            # Ultimativer Fallback falls selbst read_bytes fehlschlaegt
            self.logger.debug("Plain-Text Lesen fehlgeschlagen (%s), versuche Text mit ignore: %s", exc, path)
            try:
                return path.read_text(encoding='utf-8', errors='ignore')
            except Exception:
                return ''

    def _read_structured_text(self, path: Path) -> str:
        try:
            suffix = path.suffix.lower()
            if suffix == '.json':
                # Robust: Mehrere Encodings testen; bei fehlerhaftem JSON Rohtext zurückgeben
                raw = path.read_bytes()
                try_encodings = [
                    'utf-8', 'utf-8-sig', 'utf-16', 'utf-16-le', 'utf-16-be', 'cp1252', 'latin-1'
                ]
                first_text: Optional[str] = None
                for enc in try_encodings:
                    try:
                        txt = raw.decode(enc)
                        if first_text is None:
                            first_text = txt
                        # Versuche zu parsen
                        data = json.loads(txt)
                        return json.dumps(data, ensure_ascii=False, indent=2)
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        continue
                    except Exception:
                        continue
                # Fallback: gib decodierten Rohtext zurück (bevorzugt erstes erfolgreiches Decoding)
                if first_text is not None:
                    self.logger.debug("JSON-Datei ist nicht valide, Rohtext verwendet: %s", path)
                    return first_text
                return raw.decode('utf-8', errors='ignore')
            if suffix in {'.yaml', '.yml'}:
                with path.open('r', encoding='utf-8', errors='ignore') as handle:
                    return handle.read()
            if suffix == '.xml':
                return path.read_text(encoding='utf-8', errors='ignore')
            return ''
        except Exception as exc:
            # Ultimativer Fallback: Rohtext
            try:
                raw = path.read_bytes()
                self.logger.debug("Strukturiertes Lesen fehlgeschlagen (%s), Rohtext verwendet: %s", exc, path)
                return raw.decode('utf-8', errors='ignore')
            except Exception:
                return ''

    def _read_csv(self, path: Path) -> str:
        lines = []
        try:
            with path.open('r', encoding='utf-8', errors='ignore') as handle:
                reader = csv.reader(handle)
                for row_index, row in enumerate(reader):
                    lines.append(', '.join(row))
                    if row_index >= 200:
                        break
        except Exception:
            return path.read_text(encoding='utf-8', errors='ignore')
        return '\n'.join(lines)

    def _strip_html(self, path: Path) -> str:
        import re
        raw = path.read_text(encoding='utf-8', errors='ignore')
        no_script = re.sub(r'<script.*?>.*?</script>', '', raw, flags=re.DOTALL | re.IGNORECASE)
        no_style = re.sub(r'<style.*?>.*?</style>', '', no_script, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<[^>]+>', ' ', no_style)
        return re.sub(r'\s+', ' ', text).strip()

    def _build_header(self, path: Path) -> str:
        relative = path.relative_to(self.base_dir).as_posix()
        stat = path.stat()
        timestamp = datetime.fromtimestamp(stat.st_mtime).strftime('%d.%m.%Y %H:%M')
        return (
            f"Datei: {relative}\n"
            f"Groesse: {stat.st_size} Bytes\n"
            f"Zuletzt aktualisiert: {timestamp}"
        )

    def _load_index(self) -> None:
        if not self.index_path.exists():
            self._index_files = {}
            self._index_meta = self._default_meta()
            self._rebuild_blacklist_cache()
            return
        try:
            with self.index_path.open('r', encoding='utf-8') as handle:
                data = json.load(handle)
            if isinstance(data, dict):
                files = data.get('files')
                meta = data.get('_meta')
                if isinstance(files, dict):
                    self._index_files = files
                else:
                    # legacy manifest without meta wrapper
                    self._index_files = {k: v for k, v in data.items() if isinstance(v, dict)}
                if isinstance(meta, dict):
                    self._index_meta = self._merge_meta(meta)
                else:
                    self._index_meta = self._default_meta()
            else:
                self._index_files = {}
                self._index_meta = self._default_meta()
        except Exception as exc:
            self.logger.error("Fehler beim Laden des Import-Index: %s", exc)
            self._index_files = {}
            self._index_meta = self._default_meta()
        self._rebuild_blacklist_cache()

    def _save_index(self) -> None:
        try:
            temp_path = self.index_path.with_suffix('.tmp')
            with temp_path.open('w', encoding='utf-8') as handle:
                payload = {
                    '_meta': self._index_meta,
                    'files': self._index_files
                }
                json.dump(payload, handle, ensure_ascii=False, indent=2)
            temp_path.replace(self.index_path)
        except Exception as exc:
            self.logger.error("Fehler beim Speichern des Import-Index: %s", exc)

    def _notify(self, stage: str, **payload: Any) -> None:
        if not self.progress_callback:
            return
        data = {'stage': stage, 'source': 'local_knowledge_import'}
        data.update(payload)
        try:
            self.progress_callback(data)
        except Exception as exc:
            self.logger.error("Progress-Callback fuer Import fehlgeschlagen: %s", exc)

    # ------------------------------------------------------------------ #
    def _default_meta(self) -> Dict[str, Any]:
        return {
            'version': 2,
            'blacklist': {
                'paths': [
                    'desktop/bank',
                    'pictures/ubisoftconnect',
                    'pictures',
                ],
                'patterns': [
                    '*2fa*',
                    '*backup*code*',
                    '*config.json',
                    '*knowledge_base.json',
                    '*vector_memory.json',
                ],
            },
        }

    def _merge_meta(self, loaded: Dict[str, Any]) -> Dict[str, Any]:
        merged = self._default_meta()
        if not isinstance(loaded, dict):
            return merged
        merged['version'] = loaded.get('version', merged.get('version'))
        default_blacklist = merged.get('blacklist', {})
        loaded_blacklist = loaded.get('blacklist', {})
        if isinstance(loaded_blacklist, dict):
            for key in ('paths', 'patterns'):
                values = loaded_blacklist.get(key, [])
                if isinstance(values, list):
                    normalised = [str(entry).strip().lower() for entry in values if entry]
                    default = default_blacklist.get(key, [])
                    merged_values = list(dict.fromkeys([*(default or []), *normalised]))
                    default_blacklist[key] = merged_values
        merged['blacklist'] = default_blacklist
        return merged

    def _rebuild_blacklist_cache(self) -> None:
        cfg = self._index_meta.get('blacklist', {}) or {}
        paths = cfg.get('paths', []) or []
        patterns = cfg.get('patterns', []) or []
        self._blacklist_exact = {str(entry).strip().lower().rstrip('/') for entry in paths if entry}
        self._blacklist_patterns = tuple(str(entry).strip().lower() for entry in patterns if entry)

    def _is_blacklisted(self, relative: str) -> bool:
        rel = (relative or "").strip().lower()
        if not rel:
            return False
        for entry in self._blacklist_exact:
            if rel == entry or rel.startswith(f"{entry}/"):
                return True
        return any(fnmatch(rel, pattern) for pattern in self._blacklist_patterns)


__all__ = ["LocalKnowledgeImporter"]
