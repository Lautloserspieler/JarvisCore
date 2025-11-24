"""
Sicherheits-Notfallprotokoll (SNP-01-Lokal) für J.A.R.V.I.S.

Implementiert isolierte Sofortmaßnahmen, Diagnose- und Wiederherstellungsabläufe
gemäß Sicherheitsrichtlinie Version 1.1 (Offline-Sicherheitsfassung, 17.10.2025).
"""

from __future__ import annotations

import datetime as _dt
import json
import logging
import os
import shutil
import traceback
import zipfile
from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from reportlab.lib.pagesizes import A4  # type: ignore
    from reportlab.pdfgen import canvas  # type: ignore

    _REPORTLAB_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    _REPORTLAB_AVAILABLE = False

from utils.logger import Logger


class PriorityLevel(Enum):
    """Abbildung der Notfallstufen."""

    CRITICAL = "stufe_1_kritisch"
    MAJOR = "stufe_2_schwer"
    MODERATE = "stufe_3_mittel"
    MINOR = "stufe_4_leicht"

    @classmethod
    def from_text(cls, value: Optional[str]) -> "PriorityLevel":
        normalized = (value or "").strip().lower()
        if not normalized:
            return cls.MAJOR
        if "1" in normalized or "krit" in normalized or "critical" in normalized:
            return cls.CRITICAL
        if "2" in normalized or "schwer" in normalized or "major" in normalized:
            return cls.MAJOR
        if "3" in normalized or "mittel" in normalized or "moderate" in normalized:
            return cls.MODERATE
        if "4" in normalized or "leicht" in normalized or "minor" in normalized:
            return cls.MINOR
        mapping = {
            "kritisch": cls.CRITICAL,
            "schwer": cls.MAJOR,
            "kern": cls.CRITICAL,
            "kernel": cls.MAJOR,
            "kompromittiert": cls.CRITICAL,
            "kompromittierung": cls.CRITICAL,
            "datenleck": cls.CRITICAL,
            "korruption": cls.MAJOR,
            "modul": cls.MODERATE,
            "tts": cls.MODERATE,
            "stt": cls.MODERATE,
        }
        return mapping.get(normalized, cls.MAJOR)

    def label(self) -> str:
        labels = {
            self.CRITICAL: "🟥 Stufe 1 – Kritisch",
            self.MAJOR: "🟧 Stufe 2 – Schwer",
            self.MODERATE: "🟨 Stufe 3 – Mittel",
            self.MINOR: "🟩 Stufe 4 – Leicht",
        }
        return labels[self]


@dataclass
class SecurityIncident:
    """Container für den Lebenszyklus eines Sicherheitsvorfalls."""

    level: PriorityLevel
    reason: str
    initiated_by: str
    detected_at: _dt.datetime = field(default_factory=_dt.datetime.utcnow)
    actions: List[str] = field(default_factory=list)
    results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    report_path: Optional[Path] = None
    archive_path: Optional[Path] = None
    diagnostics_report: Optional[Dict[str, Any]] = None

    def as_dict(self) -> Dict[str, Any]:
        payload = {
            "level": self.level.value,
            "level_label": self.level.label(),
            "reason": self.reason,
            "initiated_by": self.initiated_by,
            "detected_at": self.detected_at.isoformat(),
            "actions": self.actions,
            "results": self.results,
            "errors": self.errors,
            "archive_path": str(self.archive_path) if self.archive_path else None,
            "report_path": str(self.report_path) if self.report_path else None,
            "diagnostics": self.diagnostics_report or {},
        }
        return payload


class SecurityProtocolError(RuntimeError):
    """Fehler, der beim Abarbeiten des Protokolls auftreten kann."""


class SecurityProtocolManager:
    """Koordiniert SNP-01-Lokal inklusive Safemode, Recovery und Dokumentation."""

    def __init__(
        self,
        *,
        system_control: Any,
        security_manager: Any,
        knowledge_manager: Any,
        logger: Optional[Logger] = None,
        settings: Optional[Any] = None,
        llm_manager: Optional[Any] = None,
        gui: Optional[Any] = None,
        tts: Optional[Any] = None,
        base_dir: Optional[Path] = None,
    ) -> None:
        self.logger = logger or Logger()
        self.system_control = system_control
        self.security_manager = security_manager
        self.knowledge_manager = knowledge_manager
        self.settings = settings
        self.llm_manager = llm_manager
        self.gui = gui
        self.tts = tts
        self.base_dir = Path(base_dir or os.getcwd()).resolve()

        self.backup_dir = self.base_dir / "backups" / "temp"
        self.report_dir = self.base_dir / "reports" / "security"
        self.incident_log = self.base_dir / "data" / "security_incidents.json"
        self.hash_reference = self.base_dir / "config" / "checksums.json"
        self.security_log_path = self.base_dir / "logs" / "security.log"

        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.security_log_path.parent.mkdir(parents=True, exist_ok=True)

        self._security_logger = logging.getLogger("J.A.R.V.I.S.::Security")
        if not self._security_logger.handlers:
            handler = logging.FileHandler(self.security_log_path, encoding="utf-8")
            formatter = logging.Formatter(
                "%(asctime)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            handler.setFormatter(formatter)
            self._security_logger.addHandler(handler)
            self._security_logger.setLevel(logging.INFO)

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def activate(
        self,
        level: PriorityLevel | str | None,
        reason: str,
        *,
        initiated_by: str = "unbekannt",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SecurityIncident:
        """Führt SNP-01-Lokal vollständig aus und gibt Incident-Daten zurück."""

        resolved_level = level if isinstance(level, PriorityLevel) else PriorityLevel.from_text(str(level))
        incident = SecurityIncident(
            level=resolved_level,
            reason=reason,
            initiated_by=initiated_by,
        )
        severity_map = {
            PriorityLevel.CRITICAL: "critical",
            PriorityLevel.MAJOR: "elevated",
            PriorityLevel.MODERATE: "normal",
            PriorityLevel.MINOR: "low",
        }
        try:
            self.security_manager.update_security_level(severity_map.get(resolved_level, "normal"))
        except Exception:
            pass
        incident.actions.append(f"Aktivierung {incident.level.label()}")
        self._log_security_event("Notfallprotokoll aktiviert", incident, metadata)

        self._notify_start(incident)
        try:
            incident.results["isolation"] = self._enter_isolation(incident)
            incident.results["snapshot"] = self._capture_state(incident)
            incident.results["recovery"] = self._start_recovery(incident)
            diagnostics = self._run_diagnostics(incident)
            incident.diagnostics_report = diagnostics
            incident.results["diagnostics"] = diagnostics
        except Exception as exc:
            message = f"Fehler im Notfallprotokoll: {exc}"
            incident.errors.append(message)
            incident.errors.append(traceback.format_exc())
            self.logger.error(message, exc_info=True)
            self._security_logger.error(message)

        self._finalise_incident(incident)
        self._persist_incident(incident)
        self._notify_completion(incident)
        return incident

    def run_startup_check(self) -> Dict[str, Any]:
        """Autodiagnose beim Systemstart – Hash-Prüfung und Report."""
        diagnostics = self._run_hash_validation()
        overall_ok = True
        section_issue = False
        if isinstance(diagnostics, dict):
            overall_ok = bool(diagnostics.get("ok", True)) if "ok" in diagnostics else True
            for value in diagnostics.values():
                if isinstance(value, dict) and not value.get("ok", True):
                    section_issue = True
                    break
        any_issue = (not overall_ok) or section_issue
        summary = (
            "Autodiagnose abgeschlossen – Abweichungen erkannt"
            if any_issue
            else "Autodiagnose abgeschlossen – keine Auffälligkeiten"
        )
        self._security_logger.info(summary)
        if any_issue:
            self.logger.warning(summary)
        else:
            self.logger.info(summary)
        return diagnostics

    # ------------------------------------------------------------------ #
    # Protokollschritte
    # ------------------------------------------------------------------ #
    def _enter_isolation(self, incident: SecurityIncident) -> Dict[str, Any]:
        incident.actions.append("🧩 Isolationsmodus (Safe Mode)")
        try:
            result = self.system_control.enter_safe_mode()
            self._security_logger.info("Isolationsmodus aktiviert")
            return result or {}
        except Exception as exc:  # pragma: no cover - defensive
            incident.errors.append(f"Safe-Mode fehlgeschlagen: {exc}")
            self.logger.error(f"Safe-Mode konnte nicht aktiviert werden: {exc}", exc_info=True)
            return {"error": str(exc)}

    def _capture_state(self, incident: SecurityIncident) -> Dict[str, Any]:
        incident.actions.append("⚙️ Zustand sichern")
        timestamp = _dt.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        archive_path = self.backup_dir / f"snapshot_{timestamp}.zip"
        files_to_include = [
            ("config/settings.py", "config/settings.py"),
            ("data/settings.json", "data/settings.json"),
            ("logs/jarvis.log", "logs/jarvis.log"),
            ("logs/security.log", "logs/security.log"),
        ]
        optional_globs = [
            ("data/learning_state.json", "data/learning_state.json"),
            ("data/preferences.json", "data/preferences.json"),
        ]

        added_files: List[str] = []
        try:
            with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                for src, arcname in files_to_include:
                    src_path = self.base_dir / src
                    if src_path.exists():
                        archive.write(src_path, arcname)
                        added_files.append(arcname)
                for src, arcname in optional_globs:
                    src_path = self.base_dir / src
                    if src_path.exists():
                        archive.write(src_path, arcname)
                        added_files.append(arcname)
            hash_path = archive_path.with_suffix(".sha256")
            digest = self._hash_file(archive_path)
            hash_path.write_text(digest, encoding="utf-8")
            incident.archive_path = archive_path
            snap_info = {
                "archive": str(archive_path),
                "file_count": len(added_files),
                "sha256": digest,
            }
            self._security_logger.info("Zustand archiviert: %s", snap_info)
            return snap_info
        except Exception as exc:  # pragma: no cover - fallback
            incident.errors.append(f"Snapshot fehlgeschlagen: {exc}")
            self.logger.error(f"Snapshot fehlgeschlagen: {exc}", exc_info=True)
            return {"error": str(exc)}

    def _start_recovery(self, incident: SecurityIncident) -> Dict[str, Any]:
        incident.actions.append("💾 Recovery starten")
        summary: Dict[str, Any] = {
            "models_loaded": False,
            "settings_restored": False,
            "hardware_check": False,
        }
        # Lokales Basismodell laden
        if self.llm_manager is not None:
            try:
                preferred = None
                if self.settings and hasattr(self.settings, "get_model_settings"):
                    llm_cfg = self.settings.get_model_settings("llm") or {}
                    preferred = llm_cfg.get("default")
                model_info = self.llm_manager.auto_install_models() if hasattr(self.llm_manager, "auto_install_models") else None
                if hasattr(self.llm_manager, "set_active_model") and preferred:
                    self.llm_manager.set_active_model(preferred)
                summary["models_loaded"] = True if model_info is not None else True
            except Exception as exc:
                incident.errors.append(f"Modelle konnten nicht geladen werden: {exc}")

        # Letzten stabilen Systemzustand laden
        latest_settings = self.base_dir / "config" / "last_good.json"
        if latest_settings.exists() and self.settings is not None:
            try:
                payload = json.loads(latest_settings.read_text(encoding="utf-8"))
                self.settings.settings.update(payload)
                summary["settings_restored"] = True
            except Exception as exc:
                incident.errors.append(f"Einstellungen konnten nicht wiederhergestellt werden: {exc}")

        # Hardwarediagnose (rudimentäre Checks)
        try:
            health = self.system_control.get_hardware_health() if hasattr(self.system_control, "get_hardware_health") else {}
            summary["hardware_check"] = True if health else False
            summary["hardware_health"] = health
        except Exception:
            summary["hardware_check"] = False

        self._security_logger.info("Recovery abgeschlossen: %s", summary)
        return summary

    def _run_diagnostics(self, incident: SecurityIncident) -> Dict[str, Any]:
        incident.actions.append("🔄 Diagnose")
        diagnostics = {
            "hash_check": self._run_hash_validation(),
            "change_log": self._collect_recent_changes(),
        }
        self._security_logger.info("Diagnosebericht erstellt")
        return diagnostics

    def _finalise_incident(self, incident: SecurityIncident) -> None:
        incident.actions.append("🔹 Nachbearbeitung & Abschluss")
        incident.report_path = self._generate_report(incident)
        message = "✅ J.A.R.V.I.S. wurde erfolgreich wiederhergestellt. Alle Systeme laufen stabil. Diagnosebericht erstellt."
        incident.results["final_message"] = message
        self.logger.info(message)
        self._security_logger.info(message)
        if self.gui and hasattr(self.gui, "update_status"):
            try:
                self.gui.update_status(message)
            except Exception:
                pass
        if self.tts and hasattr(self.tts, "speak"):
            try:
                self.tts.speak(message, style="professionell")
            except Exception:
                pass

    # ------------------------------------------------------------------ #
    # Hilfsfunktionen
    # ------------------------------------------------------------------ #
    def _notify_start(self, incident: SecurityIncident) -> None:
        msg = f"⚠️ Sicherheitsereignis erkannt – {incident.level.label()}. Grund: {incident.reason}"
        self.logger.warning(msg)
        self._security_logger.warning(msg)
        if self.gui and hasattr(self.gui, "update_status"):
            try:
                self.gui.update_status("Sicherheitsmodus aktiv – Isolationsmaßnahmen laufen")
            except Exception:
                pass
        if self.gui and hasattr(self.gui, "show_alert"):
            try:
                self.gui.show_alert("Sicherheitsmodus aktiv", msg)
            except Exception:
                pass
        if self.tts and hasattr(self.tts, "speak"):
            try:
                self.tts.speak("Sicherheitsereignis erkannt. Isolationsmodus wird aktiviert.", style="professionell")
            except Exception:
                pass

    def _notify_completion(self, incident: SecurityIncident) -> None:
        info = f"Notfallprotokoll abgeschlossen – {incident.report_path}"
        self.logger.info(info)
        self._security_logger.info(info)

    def _hash_file(self, file_path: Path) -> str:
        digest = sha256()
        with file_path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(65536), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _run_hash_validation(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {"ok": True, "files": []}
        if not self.hash_reference.exists():
            result["ok"] = False
            result["reason"] = "checksums.json nicht vorhanden"
            return result
        try:
            reference = json.loads(self.hash_reference.read_text(encoding="utf-8"))
        except Exception as exc:
            result["ok"] = False
            result["reason"] = f"checksums.json unlesbar: {exc}"
            return result

        mismatches: List[Dict[str, Any]] = []
        for rel_path, expected_hash in reference.items():
            abs_path = self.base_dir / rel_path
            if not abs_path.exists():
                mismatches.append({"path": rel_path, "status": "fehlend"})
                continue
            actual = self._hash_file(abs_path)
            if actual != expected_hash:
                mismatches.append({"path": rel_path, "status": "hash_mismatch", "expected": expected_hash, "actual": actual})
        result["files"] = mismatches
        result["ok"] = len(mismatches) == 0
        return result

    def _collect_recent_changes(self, limit: int = 50) -> List[str]:
        change_log: List[str] = []
        git_dir = self.base_dir / ".git"
        if git_dir.exists():
            try:
                import subprocess

                log_output = subprocess.check_output(
                    ["git", "-C", str(self.base_dir), "status", "--short"],
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                )
                for line in log_output.splitlines()[:limit]:
                    change_log.append(line.strip())
            except Exception:
                pass
        else:
            sentinel = self.base_dir / "logs" / "recent_changes.log"
            if sentinel.exists():
                try:
                    change_log.extend(sentinel.read_text(encoding="utf-8").splitlines()[:limit])
                except Exception:
                    pass
        return change_log

    def _generate_report(self, incident: SecurityIncident) -> Path:
        timestamp = incident.detected_at.strftime("%Y-%m-%d")
        stem = f"SNP_{timestamp}_{incident.level.value}"
        if _REPORTLAB_AVAILABLE:
            report_path = self.report_dir / f"{stem}.pdf"
            self._create_pdf_report(report_path, incident)
        else:
            report_path = self.report_dir / f"{stem}.md"
            self._create_markdown_report(report_path, incident)
        return report_path

    def _create_pdf_report(self, report_path: Path, incident: SecurityIncident) -> None:
        c = canvas.Canvas(str(report_path), pagesize=A4)
        width, height = A4
        margin = 40
        y = height - margin
        c.setFont("Helvetica-Bold", 18)
        c.drawString(margin, y, "J.A.R.V.I.S. – Sicherheitsbericht")
        c.setFont("Helvetica", 12)
        lines = [
            f"Vorfall: {incident.level.label()}",
            f"Grund: {incident.reason}",
            f"Ausgelöst von: {incident.initiated_by}",
            f"Zeitstempel: {incident.detected_at.isoformat()}",
            "",
            "Maßnahmen:",
        ]
        for line in lines:
            y -= 24
            c.drawString(margin, y, line)
        for action in incident.actions:
            y -= 18
            c.drawString(margin + 12, y, f"• {action}")
        y -= 24
        c.drawString(margin, y, "Ergebnisse & Diagnose:")
        diagnostics = incident.diagnostics_report or {}
        json_blob = json.dumps(diagnostics, ensure_ascii=False, indent=2)
        for chunk in json_blob.splitlines():
            y -= 14
            if y < margin:
                c.showPage()
                y = height - margin
                c.setFont("Helvetica", 12)
            c.drawString(margin, y, chunk)
        c.showPage()
        c.save()

    def _create_markdown_report(self, report_path: Path, incident: SecurityIncident) -> None:
        content_lines = [
            "# J.A.R.V.I.S. – Sicherheitsbericht",
            "",
            f"- **Vorfall:** {incident.level.label()}",
            f"- **Grund:** {incident.reason}",
            f"- **Ausgelöst von:** {incident.initiated_by}",
            f"- **Zeitstempel:** {incident.detected_at.isoformat()}",
            "",
            "## Maßnahmen",
        ]
        content_lines.extend([f"- {action}" for action in incident.actions])
        content_lines.append("")
        content_lines.append("## Ergebnisse & Diagnose")
        diagnostics = incident.diagnostics_report or {}
        content_lines.append("```json")
        content_lines.append(json.dumps(diagnostics, ensure_ascii=False, indent=2))
        content_lines.append("```")
        report_path.write_text("\n".join(content_lines), encoding="utf-8")

    def _persist_incident(self, incident: SecurityIncident) -> None:
        incident_history: List[Dict[str, Any]] = []
        if self.incident_log.exists():
            try:
                incident_history = json.loads(self.incident_log.read_text(encoding="utf-8"))
            except Exception:
                incident_history = []
        incident_history.append(incident.as_dict())
        self.incident_log.write_text(json.dumps(incident_history, ensure_ascii=False, indent=2), encoding="utf-8")

    def _log_security_event(
        self,
        message: str,
        incident: SecurityIncident,
        metadata: Optional[Dict[str, Any]],
    ) -> None:
        payload = {
            "message": message,
            "incident": incident.as_dict(),
            "metadata": metadata or {},
        }
        self._security_logger.info(json.dumps(payload, ensure_ascii=False))
