"""Local knowledge scanner for building a LocalWissen mirror."""

import json
import os
import shutil
import threading
from fnmatch import fnmatch
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple, Union

from core.sensitive_safe import SensitiveFileSafe
from utils.logger import Logger


@dataclass(frozen=True)
class ScanTarget:
    label: str
    path: Path


class LocalKnowledgeScanner:
    """Collects user documents from the local system drive into LocalWissen."""

    DEFAULT_FOLDERS: Tuple[str, ...] = (
        "Desktop",
        "Documents",
        "Dokumente",
        "Downloads",
        "Pictures",
        "Bilder",
        "Videos",
        "Music",
        "Musik"
    )

    DEFAULT_EXTENSIONS: Set[str] = {
        ".txt",
        ".md",
        ".rtf",
        ".pdf",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".csv",
        ".ppt",
        ".pptx",
        ".json",
        ".xml",
        ".yaml",
        ".yml",
        ".ini",
        ".log",
        ".html",
        ".htm",
        ".tex",
        ".odt",
        ".ods",
        ".odp"
    }

    PATH_IGNORE: Tuple[str, ...] = (
        '**/saved/crashes/**',
        '**/saved/shaderdebuginfo/**',
        '**/saved/logs/**',
        '**/saved/config/worldstate/**',
        '**/intermediate/**',
        '**/binaries/**',
        '**/.vs/**',
        '**/.git/**',
        '**/__pycache__/**',
        '**/.safe/**',
        '**/appdata/**',
        '**/pictures/ubisoftconnect/**',
        '**/desktop/bank/**',
        '**/localwissen/pictures/**',
        '**/documents/auth/**',
    )

    FILENAME_IGNORE: Tuple[str, ...] = (
        '*backup*code*.txt',
        '*backup*codes*.txt',
        '*2fa*',
        '*totp*',
        '*.pem',
        '*.key',
        '*.pfx',
        '*.crt',
        '*.der',
        'config.json',
        'knowledge_base.json',
        'vector_memory.json',
        '*license*',
        '*licence*',
        '*lizenz*',
        '*chat*log*',
        '*.chatlog',
    )

    EXT_IGNORE: Tuple[str, ...] = (
        '.exe', '.dll', '.pdb', '.uasset', '.umap', '.bin', '.pak', '.png', '.jpg', '.jpeg', '.mp4', '.zip', '.rar', '.sav', '.cache'
    )

    TEXTUAL_EXTENSIONS: Set[str] = {
        '.txt', '.md', '.rtf', '.json', '.yaml', '.yml', '.ini', '.cfg', '.csv', '.log', '.xml', '.html', '.htm'
    }

    SENSITIVE_KEYWORDS: Tuple[str, ...] = (
        'totp', 'backup code', 'backup-code', 'backupcode', '2fa', 'zweifaktor', 'secret', 'private key', 'api_key', 'client_secret', 'passwort', 'password', 'seed phrase', 'authenticator code'
    )

    MAX_SENSITIVE_SCAN_BYTES = 200000

    def __init__(
        self,
        project_root: Union[Path, str],
        *,
        logger: Optional[Logger] = None,
        target_dirs: Optional[Iterable[Union[Path, str]]] = None,
        max_file_size_mb: int = 15,
        allowed_extensions: Optional[Iterable[str]] = None,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> None:
        self.logger = logger or Logger()
        self.project_root = Path(project_root).resolve()
        self.output_dir = self.project_root / "LocalWissen"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._safe = SensitiveFileSafe(self.output_dir / ".safe", logger=self.logger)
        self._safe_scan_done = False

        self.max_file_size_bytes = max(1, max_file_size_mb) * 1024 * 1024
        self.allowed_extensions = {
            ext.lower() if ext.startswith('.') else f".{ext.lower()}"
            for ext in (allowed_extensions or self.DEFAULT_EXTENSIONS)
        }
        self._blocked_extensions = {
            (ext if ext.startswith('.') else f'.{ext}').lower()
            for ext in self.EXT_IGNORE
        }
        self.allowed_extensions -= self._blocked_extensions
        self._path_ignore_patterns = tuple(pattern.lower() for pattern in self.PATH_IGNORE)
        self._filename_ignore_patterns = tuple(pattern.lower() for pattern in self.FILENAME_IGNORE)
        self.progress_callback = progress_callback

        self._targets = self._build_targets(target_dirs)
        self._lock = threading.Lock()
        self._is_scanning = False

    def _build_targets(self, custom_dirs: Optional[Iterable[Union[Path, str]]]) -> List[ScanTarget]:
        targets: List[ScanTarget] = []
        seen: Set[str] = set()

        def _register(path: Path, label_hint: str) -> None:
            try:
                resolved = str(path.resolve()).lower()
            except Exception:
                resolved = str(path).lower()
            if resolved in seen:
                return
            seen.add(resolved)
            targets.append(ScanTarget(label=self._sanitize_label(label_hint), path=path))

        if custom_dirs:
            for entry in custom_dirs:
                p = Path(entry).expanduser()
                if p.exists() and p.is_dir():
                    _register(p, p.name)
            if targets:
                return targets

        user_profile = Path(os.environ.get("USERPROFILE", str(Path.home()))).expanduser()
        if user_profile.exists():
            for candidate in self._collect_known_folders(user_profile):
                _register(candidate, candidate.name)
            one_drive = user_profile / "OneDrive"
            if one_drive.exists():
                for candidate in self._collect_known_folders(one_drive):
                    _register(candidate, f"OneDrive_{candidate.name}")

        system_drive = Path(os.environ.get("SystemDrive", "C:")).expanduser()
        public_docs = system_drive / "Users" / "Public" / "Documents"
        if public_docs.exists():
            _register(public_docs, "PublicDocuments")

        if not targets:
            fallback = self.project_root.parent
            if fallback.exists():
                _register(fallback, fallback.name or "Root")

        return targets

    def _collect_known_folders(self, base: Path) -> List[Path]:
        return [path for path in (base / folder for folder in self.DEFAULT_FOLDERS) if path.exists() and path.is_dir()]

    def _sanitize_label(self, label: str) -> str:
        clean = ''.join(ch if ch.isalnum() or ch in ('_', '-') else '_' for ch in label)
        return clean or "root"

    @staticmethod
    def _normalise_path(path: Path) -> str:
        try:
            return path.resolve().as_posix().lower()
        except Exception:
            return path.as_posix().lower()

    def _matches_patterns(self, path_str: str, patterns: Tuple[str, ...]) -> bool:
        return any(fnmatch(path_str, pattern) or fnmatch(f"{path_str}/", pattern) for pattern in patterns)

    def scan(self) -> Dict[str, Any]:
        if not self._acquire_scan_lock():
            self.logger.debug("Local knowledge scan already running")
            return {}
        self._notify("local_scan_start", message="Lokaler Wissensscan gestartet")
        self._safe_scan_done = False

        summary = {
            'copied': 0,
            'skipped': 0,
            'errors': 0,
            'secured': self._secure_existing_localwissen_files(),
            'targets': []
        }

        try:
            for target in self._targets:
                stats = self._scan_target(target)
                summary['copied'] += stats['copied']
                summary['skipped'] += stats['skipped']
                summary['errors'] += stats['errors']
                summary['targets'].append({
                    'label': target.label,
                    'path': str(target.path),
                    **stats
                })
            self._write_manifest(summary)
            self._notify(
                "local_scan_complete",
                message=f"Lokaler Wissensscan abgeschlossen (kopiert: {summary['copied']}, uebersprungen: {summary['skipped']})",
                copied=summary['copied'],
                skipped=summary['skipped'],
                errors=summary['errors'],
                secured=summary['secured']
            )
            return summary
        finally:
            self._release_scan_lock()

    def _acquire_scan_lock(self) -> bool:
        if not self._lock.acquire(blocking=False):
            return False
        if self._is_scanning:
            self._lock.release()
            return False
        self._is_scanning = True
        self._lock.release()
        return True

    def _release_scan_lock(self) -> None:
        with self._lock:
            self._is_scanning = False

    def _scan_target(self, target: ScanTarget) -> Dict[str, int]:
        stats = {'copied': 0, 'skipped': 0, 'errors': 0}
        if not target.path.exists():
            self.logger.warning("Zielordner nicht gefunden: %s", target.path)
            return stats

        destination_root = self.output_dir / target.label
        destination_root.mkdir(parents=True, exist_ok=True)

        for root, dirs, files in os.walk(target.path):
            root_path = Path(root)
            dirs[:] = [d for d in dirs if not self._should_skip_directory(root_path / d)]
            for file_name in files:
                source = root_path / file_name
                if not self._should_copy(source):
                    stats['skipped'] += 1
                    continue
                if self._is_sensitive_content(source):
                    self.logger.warning('Sensitiver Inhalt erkannt, Datei wird ausgelassen: %s', source)
                    stats['skipped'] += 1
                    continue
                try:
                    relative = source.relative_to(target.path)
                except ValueError:
                    stats['skipped'] += 1
                    continue
                destination = destination_root / relative
                destination.parent.mkdir(parents=True, exist_ok=True)

                try:
                    if destination.exists() and self._is_same_file(source, destination):
                        stats['skipped'] += 1
                        continue
                    shutil.copy2(source, destination)
                    stats['copied'] += 1
                except Exception as exc:
                    stats['errors'] += 1
                    self.logger.error("Fehler beim Kopieren von %s: %s", source, exc)
        return stats

    def _secure_existing_localwissen_files(self) -> int:
        if self._safe_scan_done:
            return 0
        self._safe_scan_done = True
        secured = 0
        try:
            for path in self.output_dir.rglob('*'):
                if not path.is_file() or self._safe.is_safe_path(path):
                    continue
                if path.suffix.lower() not in self.TEXTUAL_EXTENSIONS:
                    continue
                if self._is_sensitive_content(path):
                    if self._safe.seal(path, reason="localwissen-mirror"):
                        secured += 1
        except Exception as exc:
            self.logger.error("Fehler beim Bereinigen des LocalWissen-Verzeichnisses: %s", exc)
        if secured:
            self.logger.warning("Sensitive Dateien aus LocalWissen verschoben: %s", secured)
        return secured

    def _should_skip_directory(self, path: Path) -> bool:
        normalised = self._normalise_path(path)
        if self._matches_patterns(normalised, self._path_ignore_patterns):
            return True
        name = path.name.lower()
        if name in {"appdata", "temp", "cache"}:
            return True
        if self._safe.is_safe_path(path):
            return True
        try:
            resolved_output = self.output_dir.resolve()
            resolved_path = path.resolve()
        except Exception:
            return False
        return resolved_output in resolved_path.parents

    def _should_copy(self, source: Path) -> bool:
        if not source.exists() or not source.is_file():
            return False
        normalised = self._normalise_path(source)
        if self._matches_patterns(normalised, self._path_ignore_patterns):
            return False
        lower_name = source.name.lower()
        if any(fnmatch(lower_name, pattern) for pattern in self._filename_ignore_patterns):
            return False
        suffix = source.suffix.lower()
        if suffix in self._blocked_extensions:
            return False
        if suffix not in self.allowed_extensions:
            return False
        try:
            size = source.stat().st_size
        except OSError:
            return False
        return size <= self.max_file_size_bytes

    def _is_sensitive_content(self, source: Path) -> bool:
        suffix = source.suffix.lower()
        if suffix not in self.TEXTUAL_EXTENSIONS:
            return False
        try:
            with source.open('rb') as handle:
                sample = handle.read(self.MAX_SENSITIVE_SCAN_BYTES)
        except Exception:
            return False
        if not sample:
            return False
        try:
            text = sample.decode('utf-8', errors='ignore').lower()
        except Exception:
            return False
        return any(keyword in text for keyword in self.SENSITIVE_KEYWORDS)

    def _is_same_file(self, source: Path, destination: Path) -> bool:
        try:
            src_stat = source.stat()
            dst_stat = destination.stat()
        except OSError:
            return False
        size_equal = src_stat.st_size == dst_stat.st_size
        time_diff = abs(src_stat.st_mtime - dst_stat.st_mtime)
        return size_equal and time_diff < 1.0

    def _write_manifest(self, summary: Dict[str, Any]) -> None:
        manifest = {
            'last_run': datetime.utcnow().isoformat(),
            'max_file_size_bytes': self.max_file_size_bytes,
            'allowed_extensions': sorted(self.allowed_extensions),
            'targets': summary.get('targets', []),
            'totals': {
                'copied': summary.get('copied', 0),
                'skipped': summary.get('skipped', 0),
                'errors': summary.get('errors', 0),
                'secured': summary.get('secured', 0),
            }
        }
        manifest_path = self.output_dir / "manifest.json"
        try:
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
        except Exception as exc:
            self.logger.error("Fehler beim Schreiben des Manifests: %s", exc)

    def _notify(self, stage: str, **payload: Any) -> None:
        if not self.progress_callback:
            return
        data = {'stage': stage}
        data.update(payload)
        try:
            self.progress_callback(data)
        except Exception as exc:
            self.logger.error("Progress-Callback fehlgeschlagen: %s", exc)


__all__ = ["LocalKnowledgeScanner", "ScanTarget"]
