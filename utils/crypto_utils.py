"""
Lightweight cryptography helpers for J.A.R.V.I.S.

Provides:
 - AES-256-GCM encryption for small payloads
 - RSA-4096 keypair generation and public key export
 - Optional DPAPI wrapping for the AES key on Windows hosts
"""
from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import Dict, Optional

from utils.logger import Logger
from utils.secure_storage import DPAPI, DPAPIError

try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding, rsa
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except Exception as exc:  # pragma: no cover - optional dependency
    raise RuntimeError(
        "cryptography package is required for CryptoSuite (pip install cryptography)"
    ) from exc


class CryptoSuite:
    """Manage AES/RSA keys and provide simple encrypt/decrypt helpers."""

    def __init__(self, base_dir: Path, *, logger: Optional[Logger] = None) -> None:
        self.logger = logger or Logger()
        self.base_dir = Path(base_dir)
        self.crypto_dir = self.base_dir / "data" / "secure" / "crypto"
        self.crypto_dir.mkdir(parents=True, exist_ok=True)
        self._aes_key_path = self.crypto_dir / "aes.key"
        self._rsa_private_path = self.crypto_dir / "rsa_private.pem"
        self._rsa_public_path = self.crypto_dir / "rsa_public.pem"
        self._aes_key: Optional[bytes] = None
        self._rsa_private = None
        self._rsa_public = None
        self._load_or_init_keys()

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def encrypt_aes(self, plaintext: bytes, *, aad: Optional[bytes] = None) -> Dict[str, str]:
        """Encrypts bytes with AES-256-GCM; returns base64 encoded fields."""
        aes_key = self._get_aes_key()
        iv = os.urandom(12)
        aesgcm = AESGCM(aes_key)
        ciphertext = aesgcm.encrypt(iv, plaintext, aad)
        return {
            "alg": "AES-256-GCM",
            "iv": base64.b64encode(iv).decode("ascii"),
            "ciphertext": base64.b64encode(ciphertext).decode("ascii"),
            "aad": base64.b64encode(aad).decode("ascii") if aad else None,
        }

    def decrypt_aes(self, payload: Dict[str, str]) -> bytes:
        """Decrypts AES-256-GCM payload produced by encrypt_aes."""
        aes_key = self._get_aes_key()
        iv = base64.b64decode(payload["iv"])
        ciphertext = base64.b64decode(payload["ciphertext"])
        aad_b64 = payload.get("aad")
        aad = base64.b64decode(aad_b64) if aad_b64 else None
        aesgcm = AESGCM(aes_key)
        return aesgcm.decrypt(iv, ciphertext, aad)

    def encrypt_rsa(self, plaintext: bytes) -> Dict[str, str]:
        """Encrypts bytes with the RSA public key using OAEP."""
        public_key = self._get_rsa_public()
        ciphertext = public_key.encrypt(
            plaintext,
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
        )
        return {
            "alg": "RSA-4096-OAEP",
            "ciphertext": base64.b64encode(ciphertext).decode("ascii"),
        }

    def decrypt_rsa(self, payload: Dict[str, str]) -> bytes:
        """Decrypts RSA payload produced by encrypt_rsa."""
        private_key = self._get_rsa_private()
        ciphertext = base64.b64decode(payload["ciphertext"])
        return private_key.decrypt(
            ciphertext,
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
        )

    def public_key_pem(self) -> str:
        """Returns the PEM encoded RSA public key."""
        public_key = self._get_rsa_public()
        pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        return pem.decode("ascii")

    def has_crypto(self) -> bool:
        """Indicates whether both AES and RSA keys are available."""
        return bool(self._aes_key) and bool(self._rsa_private) and bool(self._rsa_public)

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _load_or_init_keys(self) -> None:
        self._aes_key = self._load_or_create_aes_key()
        self._rsa_private, self._rsa_public = self._load_or_create_rsa_keys()

    def _load_or_create_aes_key(self) -> bytes:
        if self._aes_key_path.exists():
            data = self._aes_key_path.read_bytes()
            try:
                if data.startswith(b"DPAPI:"):
                    return DPAPI.unprotect(data[len(b"DPAPI:") :])
                return base64.b64decode(data)
            except Exception as exc:
                self.logger.warning("AES-Schluessel konnte nicht geladen werden: %s", exc)
        key = os.urandom(32)
        payload = base64.b64encode(key)
        try:
            payload = b"DPAPI:" + DPAPI.protect(key)
        except (DPAPIError, Exception):
            # DPAPI nicht verfuegbar oder fehlgeschlagen -> Klartext speichern
            pass
        try:
            self._aes_key_path.write_bytes(payload)
        except Exception as exc:
            self.logger.error("AES-Schluessel konnte nicht gespeichert werden: %s", exc)
        return key

    def _load_or_create_rsa_keys(self):
        private_key = None
        public_key = None
        if self._rsa_private_path.exists():
            try:
                private_key = serialization.load_pem_private_key(
                    self._rsa_private_path.read_bytes(),
                    password=None,
                )
                public_key = private_key.public_key()
            except Exception as exc:
                self.logger.warning("RSA-Schluessel konnte nicht geladen werden: %s", exc)
        if private_key and public_key:
            return private_key, public_key

        private_key = rsa.generate_private_key(public_exponent=65537, key_size=4096)
        public_key = private_key.public_key()
        try:
            self._rsa_private_path.write_bytes(
                private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption(),
                )
            )
            self._rsa_public_path.write_bytes(
                public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo,
                )
            )
        except Exception as exc:
            self.logger.error("RSA-Schluessel konnten nicht gespeichert werden: %s", exc)
        return private_key, public_key

    def _get_aes_key(self) -> bytes:
        if not self._aes_key:
            self._aes_key = self._load_or_create_aes_key()
        return self._aes_key

    def _get_rsa_private(self):
        if not self._rsa_private or not self._rsa_public:
            self._rsa_private, self._rsa_public = self._load_or_create_rsa_keys()
        return self._rsa_private

    def _get_rsa_public(self):
        if not self._rsa_public:
            self._rsa_private, self._rsa_public = self._load_or_create_rsa_keys()
        return self._rsa_public


__all__ = ["CryptoSuite"]
