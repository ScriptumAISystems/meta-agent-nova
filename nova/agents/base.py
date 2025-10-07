"""Common building blocks for Nova agents."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from ..blueprints.models import AgentBlueprint, AgentTaskSpec
from ..monitoring import logging as monitoring_logging


class AgentExecutionError(RuntimeError):
    """Raised when an agent fails to complete a task."""


@dataclass(slots=True)
class TaskExecutionReport:
    """Result of executing a single task."""

    task: AgentTaskSpec
    status: str
    details: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "task": self.task.to_dict(),
            "status": self.status,
            "details": list(self.details),
            "warnings": list(self.warnings),
        }


@dataclass(slots=True)
class AgentRunReport:
    """Aggregated execution data for an agent."""

    agent_type: str
    blueprint: AgentBlueprint
    task_reports: List[TaskExecutionReport]

    @property
    def success(self) -> bool:
        return all(report.status == "completed" for report in self.task_reports)

    def to_dict(self) -> dict:
        return {
            "agent_type": self.agent_type,
            "success": self.success,
            "tasks": [report.to_dict() for report in self.task_reports],
        }


class BaseAgent:
    """Base implementation shared by the specialised Nova agents."""

    agent_type: str = "agent"

    def __init__(self, blueprint: AgentBlueprint):
        if blueprint.agent_type != self.agent_type:
            raise ValueError(
                f"Blueprint agent type '{blueprint.agent_type}' does not match {self.agent_type}."
            )
        self.blueprint = blueprint

    def execute(self) -> AgentRunReport:
        monitoring_logging.log_info(
            f"Starting execution for agent '{self.agent_type}' with {len(self.blueprint.tasks)} tasks."
        )
        reports: List[TaskExecutionReport] = []
        for task in self.blueprint.tasks:
            report = self.execute_task(task)
            reports.append(report)
        return AgentRunReport(agent_type=self.agent_type, blueprint=self.blueprint, task_reports=reports)

    # The base implementation is intentionally simple yet fully traceable.  Subclasses
    # may override this method to inject additional side effects or validation.
    def execute_task(self, task: AgentTaskSpec) -> TaskExecutionReport:
        details: List[str] = []
        monitoring_logging.log_info(f"Executing task '{task.name}' for agent '{self.agent_type}'.")
        for step in task.steps:
            details.append(f"step-completed: {step}")
            monitoring_logging.log_info(f"    {step}")
        if not task.steps:
            warnings = ["Task has no defined steps."]
        else:
            warnings = []
        monitoring_logging.log_info(f"Finished task '{task.name}'.")
        return TaskExecutionReport(task=task, status="completed", details=details, warnings=warnings)


__all__ = [
    "AgentExecutionError",
    "AgentRunReport",
    "BaseAgent",
    "TaskExecutionReport",
]
