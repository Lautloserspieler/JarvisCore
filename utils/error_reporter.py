"""Minimaler Fehler-Reporter für J.A.R.V.I.S.

- Fängt nicht abgefangene Ausnahmen via sys.excepthook ab
- Schreibt strukturierte Reports in `data/error_reports/`
- Respektiert Settings: telemetry.error_reporting
"""
from __future__ import annotations

import sys
import os
import json
import traceback
import datetime as _dt
from pathlib import Path
from typing import Any, Dict, Optional

from utils.logger import Logger


class ErrorReporter:
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
            return sum(1 for p in self.reports_dir.glob(f"{today}_*.json"))
        except Exception:
            return 0

    def _build_payload(self, exc_type, exc_value, exc_tb) -> Dict[str, Any]:
        timestamp = _dt.datetime.now().isoformat(timespec="seconds")
        tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        return {
            "timestamp": timestamp,
            "type": getattr(exc_type, "__name__", str(exc_type)),
            "message": str(exc_value),
            "traceback": tb_str,
            "platform": sys.platform,
            "python": sys.version,
            "app": {
                "name": "J.A.R.V.I.S.",
            },
        }

    def _persist_report(self, payload: Dict[str, Any]) -> Path:
        ts = payload.get("timestamp", _dt.datetime.now().isoformat(timespec="seconds"))
        date_prefix = ts.split("T")[0] if "T" in ts else ts[:10]
        fname = f"{date_prefix}_{int(_dt.datetime.now().timestamp())}.json"
        path = self.reports_dir / fname
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def handle_exception(self, exc_type, exc_value, exc_tb):
        try:
            if not self.enabled:
                # Standard excepthook weiterreichen
                sys.__excepthook__(exc_type, exc_value, exc_tb)
                return
            if self._count_reports_today() >= self.max_reports_per_day:
                self.logger.warning("Fehlerreporting: Tageslimit erreicht — Report wird nicht persistiert")
                sys.__excepthook__(exc_type, exc_value, exc_tb)
                return

            payload = self._build_payload(exc_type, exc_value, exc_tb)
            path = self._persist_report(payload)
            self.logger.error(f"Unbehandelte Ausnahme — Report gespeichert: {path}", exc_info=(exc_type, exc_value, exc_tb))

            # Optional: Versand/Upload, falls später implementiert
            if self.send_anonymous:
                # Platzhalter für zukünftigen Versand
                self.logger.debug("Anonymer Versand ist aktiviert (nicht implementiert)")
        except Exception as err:
            # Niemals hier crashen — letzte Verteidigungslinie
            self.logger.error(f"ErrorReporter selbst fehlgeschlagen: {err}")
        finally:
            # Immer Standard excepthook ausführen, damit Traceback in Konsole bleibt
            try:
                sys.__excepthook__(exc_type, exc_value, exc_tb)
            except Exception:
                pass

    def install_global_hook(self) -> None:
        sys.excepthook = self.handle_exception


__all__ = ["ErrorReporter"]
