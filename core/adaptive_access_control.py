"""
Adaptive access control for the J.A.R.V.I.S. security layer.

Provides dynamic permission decisions based on user role, current security
level and contextual metadata (use case, task urgency, etc.).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from utils.logger import Logger


@dataclass
class AccessDecision:
    allowed: bool
    confidence: float
    reason: str
    required_role: str
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class AdaptiveAccessController:
    """Evaluates access requests against adaptive security policies."""

    ROLE_THRESHOLDS: Dict[str, float] = {
        "guest": 0.35,
        "user": 0.6,
        "power": 0.8,
        "admin": 1.0,
    }

    SECURITY_MODIFIERS: Dict[str, float] = {
        "low": 0.05,
        "normal": 0.0,
        "elevated": -0.15,
        "critical": -0.3,
    }

    BASE_RISK: Dict[str, float] = {
        "filesystem.read": 0.35,
        "filesystem.write": 0.65,
        "filesystem.delete": 0.8,
        "system.command": 0.75,
        "system.script": 0.8,
        "network.request": 0.55,
        "hardware.camera": 0.9,
        "hardware.microphone": 0.85,
    }

    CONTEXT_BOOSTS: Dict[str, float] = {
        "autonomous": 0.05,
        "diagnostics": -0.05,
        "emergency": -0.1,
        "sensitive": 0.1,
        "training": -0.05,
    }

    def __init__(self, *, default_role: str = "user", logger: Optional[Logger] = None) -> None:
        self.logger = logger or Logger()
        self.current_role = default_role if default_role in self.ROLE_THRESHOLDS else "user"
        self.security_level = "normal"
        self.dynamic_flags: Dict[str, Any] = {}
        self._history: List[AccessDecision] = []

    # ------------------------------------------------------------------ #
    # State management
    # ------------------------------------------------------------------ #
    def update_state(
        self,
        *,
        user_role: Optional[str] = None,
        security_level: Optional[str] = None,
        flags: Optional[Dict[str, Any]] = None,
    ) -> None:
        if user_role and user_role in self.ROLE_THRESHOLDS:
            if user_role != self.current_role:
                self.logger.debug(f"AdaptiveAccessController: rolle -> {user_role}")
            self.current_role = user_role
        if security_level:
            level = security_level.lower()
            if level not in self.SECURITY_MODIFIERS:
                level = "normal"
            if level != self.security_level:
                self.logger.debug(f"AdaptiveAccessController: sicherheitsstufe -> {level}")
            self.security_level = level
        if flags:
            self.dynamic_flags.update(flags)

    # ------------------------------------------------------------------ #
    # Evaluation
    # ------------------------------------------------------------------ #
    def evaluate(self, capability: str, *, metadata: Optional[Dict[str, Any]] = None) -> AccessDecision:
        metadata = metadata or {}
        risk = self._compute_risk(capability, metadata)
        threshold = self._compute_threshold()
        allowed = risk <= threshold

        # Confidence is how far below the threshold the risk lies.
        confidence = max(0.0, threshold - risk)

        required_role = self._required_role_for_risk(risk)
        reason = f"Risiko {risk:.2f} vs Schwelle {threshold:.2f}"
        tags: List[str] = []

        # Check for overrides/confirmation logic.
        confirmed = bool(metadata.get("confirmed"))
        allow_if_confirmed = bool(metadata.get("allow_if_confirmed"))
        requires_confirmation = bool(metadata.get("requires_confirmation"))

        if not allowed and allow_if_confirmed and confirmed:
            allowed = True
            tags.append("override_with_confirmation")
            reason += " (manuelle Freigabe)"
        elif allowed and requires_confirmation and not confirmed:
            allowed = False
            tags.append("requires_confirmation")
            reason += " (Bestaetigung erforderlich)"

        decision = AccessDecision(
            allowed=allowed,
            confidence=round(confidence, 3),
            reason=reason,
            required_role=required_role,
            tags=tags,
            metadata=dict(metadata),
        )
        self._history.append(decision)
        if len(self._history) > 100:
            self._history = self._history[-50:]

        self.logger.debug(
            "Adaptive decision %s | capability=%s role=%s level=%s risk=%.2f threshold=%.2f tags=%s",
            "ALLOWED" if allowed else "DENIED",
            capability,
            self.current_role,
            self.security_level,
            risk,
            threshold,
            ",".join(tags) or "-",
        )
        return decision

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _compute_risk(self, capability: str, metadata: Dict[str, Any]) -> float:
        base = self.BASE_RISK.get(capability, 0.5)
        risk = base

        context_text = " ".join(
            str(metadata.get(key, "")) for key in ("context", "use_case", "logic_path")
        ).lower()
        for keyword, boost in self.CONTEXT_BOOSTS.items():
            if keyword and keyword in context_text:
                risk += boost

        sensitivity = str(metadata.get("sensitivity", "")).lower()
        if sensitivity == "high":
            risk += 0.1
        elif sensitivity == "low":
            risk -= 0.05

        urgency = str(metadata.get("urgency", "")).lower()
        if urgency == "high":
            risk -= 0.05
        elif urgency == "low":
            risk += 0.05

        if metadata.get("automation") or self.dynamic_flags.get("autonomous_mode"):
            risk += 0.05

        if metadata.get("base_allowed") is False:
            risk += 0.2

        threat_flag = str(self.dynamic_flags.get("threat", "")).lower()
        if threat_flag in ("elevated", "critical"):
            risk += 0.1

        return max(0.0, min(1.0, risk))

    def _compute_threshold(self) -> float:
        base_threshold = self.ROLE_THRESHOLDS.get(self.current_role, 0.6)
        modifier = self.SECURITY_MODIFIERS.get(self.security_level, 0.0)
        threshold = max(0.1, min(1.0, base_threshold + modifier))
        return threshold

    def _required_role_for_risk(self, risk: float) -> str:
        for role, threshold in sorted(self.ROLE_THRESHOLDS.items(), key=lambda entry: entry[1]):
            if risk <= threshold:
                return role
        return "admin"

    # ------------------------------------------------------------------ #
    # Introspection
    # ------------------------------------------------------------------ #
    def get_history(self, limit: int = 20) -> List[AccessDecision]:
        if limit <= 0:
            return list(self._history)
        return self._history[-limit:]


__all__ = ["AdaptiveAccessController", "AccessDecision"]
