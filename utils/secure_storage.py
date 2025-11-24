"""
Utilities for securely storing sensitive data on Windows hosts.

Provides a thin wrapper around DPAPI together with small helpers that allow
other modules to persist credentials without leaving them in plain text on
disk or in memory for longer than necessary.
"""
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Optional


class DPAPIError(RuntimeError):
    """Raised when DPAPI encryption or decryption fails."""


if os.name == "nt":
    import ctypes
    from ctypes import wintypes

    class DATA_BLOB(ctypes.Structure):  # type: ignore[misc]
        _fields_ = [
            ("cbData", wintypes.DWORD),
            ("pbData", ctypes.POINTER(ctypes.c_byte)),
        ]

    _crypt32 = ctypes.windll.crypt32  # type: ignore[attr-defined]
    _kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
    _CRYPTPROTECT_UI_FORBIDDEN = 0x01

    def _make_blob(payload: bytes) -> "DATA_BLOB":
        blob = DATA_BLOB()
        buffer = ctypes.create_string_buffer(payload)
        blob.cbData = len(payload)
        blob.pbData = ctypes.cast(buffer, ctypes.POINTER(ctypes.c_byte))
        blob._buffer = buffer  # type: ignore[attr-defined]
        return blob


class DPAPI:
    """Expose Windows DPAPI operations with a simple Pythonic interface."""

    @staticmethod
    def protect(data: bytes, *, description: str = "") -> bytes:
        if os.name != "nt":
            raise DPAPIError("DPAPI is only available on Windows hosts.")
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("DPAPI.protect expects bytes.")
        blob_in = _make_blob(bytes(data))
        blob_out = DATA_BLOB()
        desc_ptr = ctypes.c_wchar_p(description) if description else None  # type: ignore[name-defined]
        result = _crypt32.CryptProtectData(  # type: ignore[name-defined]
            ctypes.byref(blob_in),
            desc_ptr,
            None,
            None,
            None,
            _CRYPTPROTECT_UI_FORBIDDEN,  # type: ignore[name-defined]
            ctypes.byref(blob_out),
        )
        if not result:
            raise DPAPIError(f"CryptProtectData failed with error {_kernel32.GetLastError()}")  # type: ignore[name-defined]
        try:
            return ctypes.string_at(blob_out.pbData, blob_out.cbData)  # type: ignore[name-defined]
        finally:
            _kernel32.LocalFree(blob_out.pbData)  # type: ignore[name-defined]

    @staticmethod
    def unprotect(data: bytes) -> bytes:
        if os.name != "nt":
            raise DPAPIError("DPAPI is only available on Windows hosts.")
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("DPAPI.unprotect expects bytes.")
        blob_in = _make_blob(bytes(data))
        blob_out = DATA_BLOB()
        result = _crypt32.CryptUnprotectData(  # type: ignore[name-defined]
            ctypes.byref(blob_in),
            None,
            None,
            None,
            None,
            _CRYPTPROTECT_UI_FORBIDDEN,  # type: ignore[name-defined]
            ctypes.byref(blob_out),
        )
        if not result:
            raise DPAPIError(f"CryptUnprotectData failed with error {_kernel32.GetLastError()}")  # type: ignore[name-defined]
        try:
            return ctypes.string_at(blob_out.pbData, blob_out.cbData)  # type: ignore[name-defined]
        finally:
            _kernel32.LocalFree(blob_out.pbData)  # type: ignore[name-defined]


class CredentialStore:
    """Persist secrets encrypted via DPAPI."""

    def __init__(self, root: Optional[Path] = None, *, description: str = "JarvisVault") -> None:
        self.root = Path(root or Path("data") / "secure" / "credentials")
        self.root.mkdir(parents=True, exist_ok=True)
        self.description = description

    def _path_for(self, key: str) -> Path:
        safe_key = key.replace("/", "_").replace("\\", "_")
        return self.root / f"{safe_key}.bin"

    def store_secret(self, key: str, secret: str) -> None:
        if not key or secret is None:
            return
        payload = secret.encode("utf-8")
        encrypted = DPAPI.protect(payload, description=f"{self.description}:{key}")
        path = self._path_for(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(encrypted)

    def has_secret(self, key: str) -> bool:
        return self._path_for(key).exists()

    def delete_secret(self, key: str) -> None:
        path = self._path_for(key)
        try:
            path.unlink(missing_ok=True)
        except TypeError:
            if path.exists():
                path.unlink()

    def retrieve_secret(self, key: str) -> Optional[str]:
        path = self._path_for(key)
        if not path.exists():
            return None
        encrypted = path.read_bytes()
        decrypted = bytearray(DPAPI.unprotect(encrypted))
        try:
            return decrypted.decode("utf-8")
        finally:
            for idx in range(len(decrypted)):
                decrypted[idx] = 0


class EphemeralSecret:
    """
    Stores a sensitive string in memory for a limited time and ensures
    that the underlying buffer is overwritten when it expires.
    """

    def __init__(self, ttl_seconds: int = 600) -> None:
        self.ttl_seconds = max(1, int(ttl_seconds))
        self._buffer = bytearray()
        self._expires_at = 0.0

    def set(self, secret: Optional[str]) -> None:
        self.clear()
        if not secret:
            return
        normalized = secret.strip()
        if not normalized:
            return
        self._buffer = bytearray(normalized.encode("utf-8"))
        self._expires_at = time.monotonic() + self.ttl_seconds

    def borrow_bytes(self) -> Optional[bytes]:
        if not self._buffer:
            return None
        if time.monotonic() >= self._expires_at:
            self.clear()
            return None
        return bytes(self._buffer)

    def get(self) -> Optional[str]:
        data = self.borrow_bytes()
        return data.decode("utf-8") if data else None

    def touch(self) -> None:
        if self._buffer:
            self._expires_at = time.monotonic() + self.ttl_seconds

    def clear(self) -> None:
        for idx in range(len(self._buffer)):
            self._buffer[idx] = 0
        self._buffer = bytearray()
        self._expires_at = 0.0


__all__ = ["CredentialStore", "DPAPI", "DPAPIError", "EphemeralSecret"]
