"""Utility-Klasse fuer TOTP-basierte Authentifizierung."""

from __future__ import annotations

import datetime
from typing import Any, Dict, Optional

import pyotp

from utils.logger import Logger
from utils.secure_storage import CredentialStore, EphemeralSecret


class AuthenticatorManager:
    """Verwaltet TOTP-Authentifizierung fuer die Weboberflaeche."""

    def __init__(self, settings: Any, *, clock_skew: int = 1) -> None:
        self.logger = Logger()
        self.settings = settings
        self.clock_skew = max(0, int(clock_skew))
        self._credential_store = CredentialStore()
        self._pending_secret = EphemeralSecret(ttl_seconds=900)
        self._totp_secret: Optional[str] = None

        security_cfg = settings.get("security", {}) if settings else {}
        self.auth_cfg = security_cfg.get("authenticator", {}) if isinstance(security_cfg, dict) else {}

        self.required = bool(self.auth_cfg.get("required", True))
        self.issuer = str(self.auth_cfg.get("issuer") or "JarvisCore")
        self.account_name = str(self.auth_cfg.get("account_name") or "JarvisCore-WebUI")
        self.vault_reference = str(self.auth_cfg.get("vault_reference") or "security_totp_secret")
        self._pending_payload: Optional[Dict[str, str]] = None

        try:
            stored = self._credential_store.retrieve_secret(self.vault_reference)
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.warning("Authenticator secret konnte nicht gelesen werden: %s", exc)
            stored = None
        if stored:
            self._totp_secret = stored

        try:
            if self.needs_setup():
                if self.settings and not self.setup_pending():
                    self.settings.set("security.authenticator.setup_pending", True)
                self._ensure_pending_payload()
            else:
                if self.settings and self.setup_pending():
                    self.settings.set("security.authenticator.setup_pending", False)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Status-Abfragen
    # ------------------------------------------------------------------
    def is_configured(self) -> bool:
        return bool(self._totp_secret)

    def needs_setup(self) -> bool:
        return bool(self.required and not self.is_configured())

    def setup_pending(self) -> bool:
        value = self.settings.get("security.authenticator.setup_pending", False) if self.settings else False
        return bool(value)

    def get_status(self) -> Dict[str, Any]:
        status = {
            "required": self.required,
            "configured": self.is_configured(),
            "setup_pending": self.setup_pending(),
            "issuer": self.issuer,
            "account_name": self.account_name,
        }
        status["needs_setup"] = self.needs_setup()
        status["pending_secret"] = self.has_pending_secret()
        if self.needs_setup():
            payload = self._ensure_pending_payload()
            if payload:
                status["pending_setup"] = dict(payload)
        return status

    # ------------------------------------------------------------------
    # Einrichtung & Verifikation
    # ------------------------------------------------------------------
    def begin_setup(self) -> Dict[str, str]:
        if self.is_configured() and not self.setup_pending():
            raise RuntimeError("Authenticator bereits eingerichtet")

        secret = pyotp.random_base32()
        self._pending_secret.set(secret)
        if self.settings:
            self.settings.set("security.authenticator.setup_pending", True)
        payload = self._build_payload(secret)
        self.logger.info("Neues Authenticator-Secret generiert")
        self._pending_payload = dict(payload)
        return payload

    def confirm_setup(self, code: str) -> bool:
        secret = self._pending_secret.get()
        if not secret:
            secret = self._totp_secret
        if not secret:
            return False
        if not self._verify_with_secret(secret, code):
            return False
        try:
            self._credential_store.store_secret(self.vault_reference, secret)
            self._totp_secret = secret
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error("Authenticator secret konnte nicht gespeichert werden: %s", exc)
            return False
        finally:
            self._pending_secret.clear()
            self._pending_payload = None

        if self.settings:
            self.settings.set("security.authenticator.configured", True)
            self.settings.set("security.authenticator.setup_pending", False)
            self.settings.set(
                "security.authenticator.configured_at",
                datetime.datetime.utcnow().isoformat(),
            )
        self.logger.info("Authenticator erfolgreich eingerichtet")
        return True

    def verify(self, code: str) -> bool:
        secret = self._totp_secret
        if not secret:
            try:
                secret = self._credential_store.retrieve_secret(self.vault_reference)
            except Exception as exc:  # pragma: no cover - defensive
                self.logger.warning("Authenticator secret konnte nicht geladen werden: %s", exc)
                return False
            if secret:
                self._totp_secret = secret
        if not secret:
            return False
        return self._verify_with_secret(secret, code)

    # ------------------------------------------------------------------
    # Interne Helfer
    # ------------------------------------------------------------------
    def _verify_with_secret(self, secret: str, code: str) -> bool:
        if not code or not isinstance(code, str):
            return False
        totp = pyotp.TOTP(secret)
        try:
            valid = bool(totp.verify(code.strip(), valid_window=self.clock_skew))
        except Exception:  # pragma: no cover - defensive
            return False
        return valid

    def has_pending_secret(self) -> bool:
        return bool(self._pending_secret.borrow_bytes())

    def get_pending_setup(self) -> Optional[Dict[str, str]]:
        payload = self._ensure_pending_payload()
        return dict(payload) if payload else None

    def _build_payload(self, secret: str) -> Dict[str, str]:
        uri = pyotp.TOTP(secret).provisioning_uri(name=self.account_name, issuer_name=self.issuer)
        return {
            "secret": secret,
            "provisioning_uri": uri,
            "issuer": self.issuer,
            "account": self.account_name,
        }

    def _ensure_pending_payload(self) -> Optional[Dict[str, str]]:
        if not self.needs_setup():
            self._pending_payload = None
            self._pending_secret.clear()
            return None
        secret_bytes = self._pending_secret.borrow_bytes()
        secret = None
        if secret_bytes:
            secret = secret_bytes.decode("utf-8")
        if not secret:
            secret = pyotp.random_base32()
            self._pending_secret.set(secret)
        if not self._pending_payload or self._pending_payload.get("secret") != secret:
            self._pending_payload = self._build_payload(secret)
        return self._pending_payload
