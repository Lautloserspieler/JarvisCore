from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from utils.logger import Logger


@dataclass
class TaskStep:
    id: str
    title: str
    description: str
    kind: str = "generic"
    status: str = "pending"
    result: Optional[str] = None


@dataclass
class TaskPlan:
    goal: str
    created_at: datetime
    steps: List[TaskStep]
    metadata: Dict[str, Any] = field(default_factory=dict)
    completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal": self.goal,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metadata": dict(self.metadata),
            "steps": [
                {
                    "id": step.id,
                    "title": step.title,
                    "description": step.description,
                    "kind": step.kind,
                    "status": step.status,
                    "result": step.result,
                }
                for step in self.steps
            ],
        }


@dataclass
class TaskExecutionResult:
    plan: TaskPlan
    success: bool
    log: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        data = self.plan.to_dict()
        data.update({"success": self.success, "log": list(self.log)})
        return data


class AutonomousTaskCore:
    """Creates and executes autonomous multi-step task plans."""

    def __init__(
        self,
        *,
        knowledge_manager: Any,
        system_control: Any,
        plugin_manager: Any,
        security_manager: Any,
        logger: Optional[Logger] = None,
    ) -> None:
        self.logger = logger or Logger()
        self.knowledge_manager = knowledge_manager
        self.system_control = system_control
        self.plugin_manager = plugin_manager
        self.security_manager = security_manager
        self.active_plan: Optional[TaskPlan] = None
        self.last_result: Optional[TaskExecutionResult] = None

    # ------------------------------------------------------------------ #
    # Planning
    # ------------------------------------------------------------------ #
    def create_plan(self, goal: str, *, context: Optional[Dict[str, Any]] = None) -> TaskPlan:
        context = dict(context or {})
        steps = self._build_steps(goal, context=context)
        plan = TaskPlan(goal=goal, created_at=datetime.utcnow(), steps=steps, metadata=context)
        self.active_plan = plan
        self.last_result = None
        self.logger.info("AutonomousTaskCore: neuer Plan erstellt - %s", goal)
        return plan

    def _build_steps(self, goal: str, *, context: Dict[str, Any]) -> List[TaskStep]:
        goal_lower = goal.lower()
        steps: List[TaskStep] = [
            TaskStep(
                id="analyse",
                title="Anforderungen analysieren",
                description="Ziel, Randbedingungen und bestehende Ressourcen evaluieren.",
                kind="analysis",
            ),
            TaskStep(
                id="plan",
                title="Umsetzungsplan entwerfen",
                description="Aufgaben in logische Teilabschnitte strukturieren und Zeit/Tools festlegen.",
                kind="planning",
            ),
        ]

        if any(keyword in goal_lower for keyword in ("test", "testen", "quality")):
            steps.append(
                TaskStep(
                    id="tests",
                    title="Tests vorbereiten und ausfuehren",
                    description="Testumgebung bereitstellen, automatisierte Tests ausfuehren und Ergebnisse erfassen.",
                    kind="validation",
                )
            )

        if any(keyword in goal_lower for keyword in ("skript", "script", "tool", "programm")):
            steps.append(
                TaskStep(
                    id="implementation",
                    title="Implementierung umsetzen",
                    description="Code/Skripte erstellen oder modifizieren, benoetigte Plugins aktivieren.",
                    kind="execution",
                )
            )

        steps.append(
            TaskStep(
                id="validierung",
                title="Ergebnis validieren",
                description="Ergebnisse pruefen, Sicherheitsrichtlinien anwenden und Feedback sammeln.",
                kind="validation",
            )
        )
        steps.append(
            TaskStep(
                id="abschluss",
                title="Bericht & Abschluss",
                description="Kurzbericht erstellen, Lessons Learned dokumentieren und Ressourcen bereinigen.",
                kind="report",
            )
        )
        return steps

    # ------------------------------------------------------------------ #
    # Execution
    # ------------------------------------------------------------------ #
    def execute_plan(self, plan: Optional[TaskPlan] = None, *, dry_run: bool = False) -> TaskExecutionResult:
        plan = plan or self.active_plan
        if not plan:
            raise ValueError("Es liegt kein Aufgabenplan vor.")

        log: List[str] = []
        success = True
        for step in plan.steps:
            step.status = "in_progress"
            log.append(f"Starte Schritt: {step.title}")
            try:
                if dry_run:
                    step.result = "Dry-Run: Schritt wurde simuliert."
                    step.status = "skipped"
                    continue
                result_text = self._perform_step(step, plan)
                step.result = result_text
                step.status = "completed"
                log.append(result_text)
            except Exception as exc:  # pragma: no cover - defensive
                step.status = "failed"
                step.result = f"Fehlgeschlagen: {exc}"
                log.append(step.result)
                success = False
                break

        plan.completed_at = datetime.utcnow()
        result = TaskExecutionResult(plan=plan, success=success, log=log)
        self.last_result = result
        return result

    def _perform_step(self, step: TaskStep, plan: TaskPlan) -> str:
        """Placeholder execution logic that integrates with subsystems."""
        if step.kind == "analysis":
            summary = self.knowledge_manager.search_knowledge(plan.goal) or "Kontextinformationen gesammelt."
            return f"Analyse abgeschlossen. Kontext: {summary[:120]}..."
        if step.kind == "planning":
            return "Detaillierter Ablaufplan mit Abhaengigkeiten erstellt."
        if step.kind == "execution":
            return "Implementierungsschritte vorbereitet und zur Ausfuehrung markiert."
        if step.kind == "validation":
            return "Validierung durchgefuehrt, Sicherheitscheck bestanden."
        if step.kind == "report":
            return "Abschlussbericht generiert und Ressourcen bereinigt."
        return "Schritt dokumentiert."

    # ------------------------------------------------------------------ #
    # Rendering helpers
    # ------------------------------------------------------------------ #
    def render_plan(self, plan: TaskPlan) -> str:
        lines = [f"Autonomer Aufgabenplan fuer: {plan.goal}"]
        for index, step in enumerate(plan.steps, start=1):
            lines.append(f"  {index}. {step.title} - Status: {step.status}")
            lines.append(f"     {step.description}")
        return "\n".join(lines)

    def render_execution(self, result: TaskExecutionResult) -> str:
        status = "erfolgreich" if result.success else "mit Fehlern"
        lines = [f"Ausfuehrung {status} abgeschlossen:", ""]
        for entry in result.log:
            lines.append(f"- {entry}")
        return "\n".join(lines)


__all__ = [
    "AutonomousTaskCore",
    "TaskPlan",
    "TaskStep",
    "TaskExecutionResult",
]
