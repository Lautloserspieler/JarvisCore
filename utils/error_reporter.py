"""Minimaler Fehler-Reporter fuer J.A.R.V.I.S.

- Faengt nicht abgefangene Ausnahmen via sys.excepthook ab
- Schreibt strukturierte Reports in `data/error_reports/`
- Respektiert Settings: telemetry.error_reporting
"""
from __future__ import annotations

import datetime as _dt
import json
import sys
import traceback
from pathlib import Path
from types import TracebackType
from typing import Any, Dict, Optional, Type

from utils.logger import Logger


class ErrorReporter:
    """Persistiert unbehandelte Ausnahmen lokal, ohne die App hart zu beenden."""

    def __init__(self, settings: Optional[Any] = None) -> None:
        self.logger = Logger()
        self.settings = settings
        self.reports_dir = Path("data/error_reports")
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        cfg = (settings.get("telemetry", {}) if settings else {}).get("error_reporting", {})
        self.enabled: bool = bool(cfg.get("enabled", True))
        self.send_anonymous: bool = bool(cfg.get("send_anonymous", False))
        self.max_reports_per_day: int = int(cfg.get("max_reports_per_day", 25))

    def _count_reports_today(self) -> int:
        today = _dt.date.today().isoformat()
        try:
            return sum(1 for _ in self.reports_dir.glob(f"{today}_*.json"))
        except Exception:
            return 0

    def _build_payload(
        self,
        exc_type: Type[BaseException],
        exc_value: BaseException,
        exc_tb: TracebackType,
    ) -> Dict[str, Any]:
        timestamp = _dt.datetime.now().isoformat(timespec="seconds")
        tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        return {
            "timestamp": timestamp,
            "type": getattr(exc_type, "__name__", str(exc_type)),
            "message": str(exc_value),
            "traceback": tb_str,
            "platform": sys.platform,
            "python": sys.version,
            "app": {"name": "J.A.R.V.I.S."},
        }

    def _persist_report(self, payload: Dict[str, Any]) -> Path:
        ts = payload.get("timestamp", _dt.datetime.now().isoformat(timespec="seconds"))
        date_prefix = ts.split("T")[0] if "T" in ts else ts[:10]
        fname = f"{date_prefix}_{int(_dt.datetime.now().timestamp())}.json"
        path = self.reports_dir / fname
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def handle_exception(
        self,
        exc_type: Type[BaseException],
        exc_value: BaseException,
        exc_tb: TracebackType,
    ) -> None:
        """Persistiert die Ausnahme und reicht sie an den Standard-Handler weiter."""
        try:
            if not self.enabled:
                sys.__excepthook__(exc_type, exc_value, exc_tb)
                return
            if self.max_reports_per_day > 0 and self._count_reports_today() >= self.max_reports_per_day:
                self.logger.warning("Fehlerreporting: Tageslimit erreicht - Report wird nicht persistiert")
                sys.__excepthook__(exc_type, exc_value, exc_tb)
                return

            payload = self._build_payload(exc_type, exc_value, exc_tb)
            path = self._persist_report(payload)
            self.logger.error(
                "Unbehandelte Ausnahme - Report gespeichert: %s",
                path,
                exc_info=(exc_type, exc_value, exc_tb),
            )

            if self.send_anonymous:
                # Geplanter Erweiterungspunkt fuer anonymen Versand
                self.logger.debug("Anonymer Versand ist aktiviert (noch nicht implementiert)")
        except Exception as err:
            # Letzte Verteidigungslinie: Fehler beim Fehlerreporting ebenfalls loggen
            self.logger.error("ErrorReporter selbst fehlgeschlagen: %s", err)
        finally:
            # Immer Standard excepthook ausfuehren, damit Traceback in Konsole bleibt
            try:
                sys.__excepthook__(exc_type, exc_value, exc_tb)
            except Exception:
                pass

    def install_global_hook(self) -> None:
        """Registriert den ErrorReporter als globalen Exception-Hook."""
        sys.excepthook = self.handle_exception


__all__ = ["ErrorReporter"]
