"""Security management for J.A.R.V.I.S."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Optional, Union, List

from utils.logger import Logger
from .adaptive_access_control import AdaptiveAccessController, AccessDecision


@dataclass
class SecurityDecision:
    action: str
    path: Optional[Path]
    allowed: bool
    reason: str = ""


class SecurityManager:
    """Central guard that validates sensitive operations."""

    def __init__(self, settings):
        self.logger = Logger()
        self._settings = settings
        self._lock = threading.Lock()

        security_cfg = settings.get("security", {}) or {}
        self.audit_enabled = bool(security_cfg.get("audit_logging", True))

        self.read_cfg = security_cfg.get("read", {}) or {}
        self.write_cfg = security_cfg.get("write", {}) or {}
        self.automation_cfg = security_cfg.get("automation", {}) or {}

        self.allowed_read_dirs = list(self._normalise_paths(self.read_cfg.get("allowed_directories", [])))
        self.denied_read_dirs = list(self._normalise_paths(self.read_cfg.get("denied_directories", [])))
        self.max_read_size_bytes = max(0, int(float(self.read_cfg.get("max_file_size_mb", 8)) * 1024 * 1024))

        self.allowed_write_dirs = list(self._normalise_paths(self.write_cfg.get("allowed_directories", [])))
        self.denied_write_dirs = list(self._normalise_paths(self.write_cfg.get("denied_directories", [])))
        self.write_require_confirmation = bool(self.write_cfg.get("require_confirmation", True))
        self.command_whitelist = self._coerce_command_whitelist(self.write_cfg.get("command_whitelist", {}))
        self.script_whitelist = list(self._normalise_paths(self.write_cfg.get("script_whitelist", [])))

        self.allow_workflows = bool(self.automation_cfg.get("allow_workflows", False))
        self.workflow_max_steps = int(self.automation_cfg.get("max_steps", 0) or 0)
        self.automation_require_confirmation = bool(self.automation_cfg.get("require_confirmation", True))

        default_role = str(security_cfg.get("default_role", "user")).lower()
        default_level = str(security_cfg.get("default_security_level", "normal")).lower()
        self.access_controller = AdaptiveAccessController(default_role=default_role, logger=self.logger)
        self.access_controller.update_state(security_level=default_level)
        self._current_context: Dict[str, Any] = {}
        self._decision_log: List[AccessDecision] = []

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------
    def set_user_role(self, role: str) -> None:
        """Passt die aktuelle Sicherheitsrolle (z.B. user/power/admin) an."""
        self.access_controller.update_state(user_role=str(role).lower())

    def update_security_level(self, level: str) -> None:
        """Informiert den adaptiven Controller über die aktuelle Gefahrenstufe."""
        self.access_controller.update_state(security_level=str(level).lower())

    def update_access_context(self, context: Optional[Dict[str, Any]] = None) -> None:
        """Aktualisiert Kontextsignale (z.B. Use-Case, Task, Stimmung)."""
        if not context:
            return
        normalised = {str(key): str(value) for key, value in context.items()}
        self._current_context.update(normalised)
        self.access_controller.update_state(flags=normalised)

    def get_access_history(self, limit: int = 20) -> List[AccessDecision]:
        """Gibt die letzten adaptiven Entscheidungen zurück."""
        return self.access_controller.get_history(limit)

    def ensure_path_permission(self, action: str, raw_path: Union[Path, str], **kwargs) -> Path:
        if action == "read":
            return self._ensure_read_permission(raw_path)
        if action == "write":
            return self.ensure_write_permission(raw_path, **kwargs)
        raise PermissionError(f"Unsupported action '{action}'")

    def ensure_write_permission(
        self,
        raw_path: Union[Path, str],
        *,
        confirmed: bool = False,
        require_exists: bool = False,
        check_parent: bool = False,
        action: str = "write",
    ) -> Path:
        path = self._resolve_path(raw_path)
        parent = path.parent if path.parent != path else path

        if require_exists and not path.exists():
            self._audit(SecurityDecision(action, path, False, "target missing"))
            raise FileNotFoundError(f"{path} does not exist")

        if path.exists() and not self._is_path_allowed(path, self.allowed_write_dirs, self.denied_write_dirs):
            self._audit(SecurityDecision(action, path, False, "path not permitted"))
            raise PermissionError(f"Write access to {path} is not permitted by security policy.")

        # Always check the parent directory to prevent writing outside the sandbox
        parent_to_check = parent
        if check_parent or not path.exists():
            if not self._is_path_allowed(parent_to_check, self.allowed_write_dirs, self.denied_write_dirs):
                self._audit(SecurityDecision(action, parent_to_check, False, "parent not permitted"))
                raise PermissionError(f"Write access to {parent_to_check} is not permitted by security policy.")

        if self.write_require_confirmation and not confirmed:
            self._audit(SecurityDecision(action, path, False, "confirmation required"))
            raise PermissionError("Write action requires explicit confirmation.")

        decision = self._evaluate_adaptive(
            "filesystem.write",
            path=path,
            extra={
                "action": action,
                "confirmed": confirmed,
                "requires_confirmation": self.write_require_confirmation,
                "sensitivity": self.write_cfg.get("sensitivity", "normal"),
            },
        )
        if not decision.allowed:
            self._audit(SecurityDecision(action, path, False, f"adaptive:{decision.reason}"))
            raise PermissionError(decision.reason)

        self._audit(SecurityDecision(action, path, True, f"adaptive:{decision.reason}"))
        return path

    def ensure_command_allowed(self, command_name: str, *, confirmed: bool = False) -> str:
        command = self.command_whitelist.get(command_name)
        if not command:
            self._audit(SecurityDecision("command", None, False, f"command '{command_name}' not whitelisted"))
            raise PermissionError(f"Command '{command_name}' is not whitelisted.")
        if self.write_require_confirmation and not confirmed:
            self._audit(SecurityDecision("command", None, False, "confirmation required"))
            raise PermissionError("Running commands requires explicit confirmation.")

        decision = self._evaluate_adaptive(
            "system.command",
            extra={
                "command": command_name,
                "confirmed": confirmed,
                "requires_confirmation": self.write_require_confirmation,
            },
        )
        if not decision.allowed:
            self._audit(SecurityDecision("command", None, False, f"adaptive:{decision.reason}"))
            raise PermissionError(decision.reason)

        self._audit(SecurityDecision("command", None, True, f"adaptive:{decision.reason}"))
        return command

    def ensure_script_allowed(self, script_path: Union[Path, str], *, confirmed: bool = False) -> Path:
        resolved = self._resolve_path(script_path)
        if resolved not in self.script_whitelist:
            self._audit(SecurityDecision("script", resolved, False, "script not whitelisted"))
            raise PermissionError(f"Script '{resolved}' is not whitelisted.")
        if self.write_require_confirmation and not confirmed:
            self._audit(SecurityDecision("script", resolved, False, "confirmation required"))
            raise PermissionError("Executing scripts requires explicit confirmation.")

        decision = self._evaluate_adaptive(
            "system.script",
            path=resolved,
            extra={
                "confirmed": confirmed,
                "requires_confirmation": self.write_require_confirmation,
            },
        )
        if not decision.allowed:
            self._audit(SecurityDecision("script", resolved, False, f"adaptive:{decision.reason}"))
            raise PermissionError(decision.reason)

        self._audit(SecurityDecision("script", resolved, True, f"adaptive:{decision.reason}"))
        return resolved

    def ensure_workflow_allowed(self, steps_count: int, *, confirmed: bool = False) -> None:
        if not self.allow_workflows:
            self.logger.warning("Workflow abgelehnt: Automationen sind in der aktuellen Policy deaktiviert.")
            self._audit(SecurityDecision("workflow", None, False, "workflows disabled"))
            raise PermissionError("Workflow execution is disabled by the security policy.")
        if self.workflow_max_steps and steps_count > self.workflow_max_steps:
            self.logger.warning(
                "Workflow abgelehnt: %s Schritte angefordert, erlaubt sind maximal %s.",
                steps_count,
                self.workflow_max_steps,
            )
            self._audit(SecurityDecision("workflow", None, False, "too many steps"))
            raise PermissionError(
                f"Workflow contains {steps_count} steps but only {self.workflow_max_steps} are allowed."
            )
        if self.automation_require_confirmation and not confirmed:
            self.logger.warning("Workflow abgelehnt: fehlende Bestaetigung fuer Automationen.")
            self._audit(SecurityDecision("workflow", None, False, "confirmation required"))
            raise PermissionError("Workflow execution requires explicit confirmation.")
        self._audit(SecurityDecision("workflow", None, True, f"steps={steps_count}"))

    def enforce_file_size_limit(self, path: Path, size_bytes: int) -> None:
        if self.max_read_size_bytes and size_bytes > self.max_read_size_bytes:
            self._audit(SecurityDecision("read", path, False, "file too large"))
            raise PermissionError(
                f"File {path} exceeds the maximum allowed size of {self.max_read_size_bytes} bytes"
            )

    def can(self, capability: str) -> bool:
        mapping = {
            "system_info": bool(self.read_cfg.get("allow_system_info", True)),
            "process_listing": bool(self.read_cfg.get("allow_process_listing", True)),
            "network_info": bool(self.read_cfg.get("allow_network_info", True)),
            "event_logs": bool(self.read_cfg.get("allow_event_logs", False)),
            "window_introspection": bool(self.read_cfg.get("allow_window_introspection", False)),
            "screenshots": bool(self.read_cfg.get("allow_screenshots", False)),
        }
        base_allowed = mapping.get(capability, False)
        decision = self._evaluate_adaptive(
            f"capability.{capability}",
            extra={"capability": capability, "base_allowed": base_allowed},
        )
        return decision.allowed

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _evaluate_adaptive(
        self,
        capability: str,
        *,
        path: Optional[Path] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> AccessDecision:
        metadata: Dict[str, Any] = dict(self._current_context)
        if path is not None:
            metadata['path'] = str(path)
        if extra:
            metadata.update(extra)
        decision = self.access_controller.evaluate(capability, metadata=metadata)
        self._decision_log.append(decision)
        if len(self._decision_log) > 100:
            self._decision_log = self._decision_log[-50:]
        return decision


    def _ensure_read_permission(self, raw_path: Union[Path, str]) -> Path:
        path = self._resolve_path(raw_path)
        if not self._is_path_allowed(path, self.allowed_read_dirs, self.denied_read_dirs):
            self._audit(SecurityDecision("read", path, False, "path not permitted"))
            raise PermissionError(f"Read access to {path} is not permitted by security policy.")

        decision = self._evaluate_adaptive("filesystem.read", path=path)
        if not decision.allowed:
            self._audit(SecurityDecision("read", path, False, f"adaptive:{decision.reason}"))
            raise PermissionError(decision.reason)

        self._audit(SecurityDecision("read", path, True, f"adaptive:{decision.reason}"))
        return path

    def _resolve_path(self, raw: Union[Path, str]) -> Path:
        path = Path(raw).expanduser()
        if not path.is_absolute():
            path = Path.cwd() / path
        try:
            return path.resolve(strict=False)
        except Exception:
            return path.absolute()

    def _is_path_allowed(self, path: Path, allowed: Iterable[Path], denied: Iterable[Path]) -> bool:
        if any(self._is_parent(denied_path, path) for denied_path in denied):
            return False
        if not allowed:
            return True
        return any(self._is_parent(allowed_path, path) for allowed_path in allowed)

    def _normalise_paths(self, raw_paths: Iterable[str]) -> Iterable[Path]:
        resolved = []
        for entry in raw_paths:
            try:
                resolved.append(self._resolve_path(entry))
            except Exception as exc:
                self.logger.warning(f"Could not normalise security path '{entry}': {exc}")
        return resolved

    @staticmethod
    def _is_parent(parent: Path, child: Path) -> bool:
        parent = parent.resolve(strict=False)
        child = child.resolve(strict=False)
        try:
            child.relative_to(parent)
            return True
        except ValueError:
            return parent == child

    def _coerce_command_whitelist(self, raw) -> Dict[str, str]:
        result: Dict[str, str] = {}
        if isinstance(raw, dict):
            for name, command in raw.items():
                if isinstance(name, str) and isinstance(command, str):
                    result[name] = command
        elif isinstance(raw, (list, tuple)):
            for command in raw:
                if isinstance(command, str):
                    result[command] = command
        return result

    def _audit(self, decision: SecurityDecision) -> None:
        if not self.audit_enabled:
            return
        status = "ALLOWED" if decision.allowed else "DENIED"
        location = str(decision.path) if decision.path else "-"
        message = f"SECURITY {status} - action={decision.action} path={location}"
        if decision.reason:
            message += f" reason={decision.reason}"
        with self._lock:
            self.logger.info(message)
