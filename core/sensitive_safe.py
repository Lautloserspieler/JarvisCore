"""
Secure container that relocates sensitive LocalWissen artifacts into an
encrypted vault backed by DPAPI.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

from utils.logger import Logger
from utils.secure_storage import DPAPI, DPAPIError


class SensitiveFileSafe:
    """Encrypt and store mirrored files that were flagged as sensitive."""

    def __init__(self, safe_root: Path, *, logger: Optional[Logger] = None) -> None:
        self.logger = logger or Logger()
        self.root = Path(safe_root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.manifest_path = self.root / "manifest.json"
        self._entries: Dict[str, Dict[str, Any]] = self._load_manifest()

    # ------------------------------------------------------------------ #
    def _load_manifest(self) -> Dict[str, Dict[str, Any]]:
        if not self.manifest_path.exists():
            return {}
        try:
            data = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except Exception as exc:
            self.logger.error("Safe-Manifest konnte nicht geladen werden: %s", exc)
        return {}

    def _save_manifest(self) -> None:
        try:
            payload = json.dumps(self._entries, ensure_ascii=False, indent=2)
            self.manifest_path.write_text(payload, encoding="utf-8")
        except Exception as exc:
            self.logger.error("Safe-Manifest konnte nicht gespeichert werden: %s", exc)

    def is_safe_path(self, path: Path) -> bool:
        try:
            return self.root in path.resolve().parents or path.resolve() == self.root
        except Exception:
            return False

    # ------------------------------------------------------------------ #
    def seal(self, source: Path, *, reason: str = "") -> bool:
        """Encrypt the file into the safe and remove the readable copy."""
        path = Path(source)
        if not path.exists() or not path.is_file():
            return False
        if self.is_safe_path(path):
            return False
        try:
            stat = path.stat()
        except OSError as exc:
            self.logger.error("Kann Datei nicht sichern (%s): %s", path, exc)
            return False

        identifier = hashlib.sha256(f"{path}|{stat.st_mtime}|{stat.st_size}".encode("utf-8")).hexdigest()
        safe_file = self.root / f"{identifier}.bin"

        try:
            raw = bytearray(path.read_bytes())
        except OSError as exc:
            self.logger.error("Lesen der sensitiven Datei fehlgeschlagen (%s): %s", path, exc)
            return False

        try:
            encrypted = DPAPI.protect(bytes(raw), description="JarvisLocalWissenSafe")
        except DPAPIError as exc:
            self.logger.error("DPAPI-Verschluesselung fehlgeschlagen (%s): %s", path, exc)
            self._zero_buffer(raw)
            return False

        digest = hashlib.sha256(bytes(raw)).hexdigest()
        self._zero_buffer(raw)

        try:
            safe_file.write_bytes(encrypted)
        except OSError as exc:
            self.logger.error("Konnte Safe-Datei nicht schreiben (%s): %s", safe_file, exc)
            return False

        try:
            path.unlink()
        except OSError as exc:
            self.logger.warning("Konnte Originaldatei nicht entfernen (%s): %s", path, exc)

        self._entries[identifier] = {
            "original_path": str(path),
            "reason": reason or "sensitive-keyword",
            "size": stat.st_size,
            "sha256": digest,
            "sealed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        self._save_manifest()
        self.logger.warning("Sensitive Datei verschoben in Safe: %s", path)
        return True

    # ------------------------------------------------------------------ #
    @staticmethod
    def _zero_buffer(buffer: bytearray) -> None:
        for idx in range(len(buffer)):
            buffer[idx] = 0


__all__ = ["SensitiveFileSafe"]
