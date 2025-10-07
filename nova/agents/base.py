"""Common building blocks for Nova agents."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Sequence

from ..blueprints.models import AgentBlueprint, AgentTaskSpec
from ..monitoring import logging as monitoring_logging
from ..system.communication import AgentMessage, CommunicationHub


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
    pre_run_messages: List[AgentMessage] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return all(report.status == "completed" for report in self.task_reports)

    def to_dict(self) -> dict:
        return {
            "agent_type": self.agent_type,
            "success": self.success,
            "tasks": [report.to_dict() for report in self.task_reports],
            "pre_run_messages": [message.to_dict() for message in self.pre_run_messages],
        }

    def to_markdown(self) -> str:
        lines = [
            f"### Agent `{self.agent_type}`",
            f"* Status: {'success' if self.success else 'issues detected'}",
        ]
        if self.pre_run_messages:
            lines.append("* Incoming instructions:")
            for message in self.pre_run_messages:
                lines.append(
                    "  - "
                    + message.subject
                    + (f" ({message.body})" if message.body else "")
                )
        if not self.task_reports:
            lines.append("* No tasks executed.")
        for task_report in self.task_reports:
            lines.append(f"- **{task_report.task.name}** → {task_report.status}")
            if task_report.warnings:
                lines.append(
                    "  - Warnings: " + ", ".join(task_report.warnings)
                )
        return "\n".join(lines)


class BaseAgent:
    """Base implementation shared by the specialised Nova agents."""

    agent_type: str = "agent"

    def __init__(
        self,
        blueprint: AgentBlueprint,
        *,
        communication_hub: CommunicationHub | None = None,
    ):
        if blueprint.agent_type != self.agent_type:
            raise ValueError(
                f"Blueprint agent type '{blueprint.agent_type}' does not match {self.agent_type}."
            )
        self.blueprint = blueprint
        self.communication_hub = communication_hub

    def execute(self) -> AgentRunReport:
        monitoring_logging.log_info(
            f"Starting execution for agent '{self.agent_type}' with {len(self.blueprint.tasks)} tasks."
        )
        reports: List[TaskExecutionReport] = []
        pre_run_messages = self._collect_instructions()
        for task in self.blueprint.tasks:
            report = self.execute_task(task)
            reports.append(report)
        return AgentRunReport(
            agent_type=self.agent_type,
            blueprint=self.blueprint,
            task_reports=reports,
            pre_run_messages=pre_run_messages,
        )

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
        status = "completed"
        message = self.emit_message(
            subject=f"task-completed::{task.name}",
            body=f"Task '{task.name}' completed with status {status}.",
            recipients=("orchestrator",),
            metadata={
                "task": task.name,
                "goal": task.goal,
                "outputs": list(task.outputs),
                "warnings": list(warnings),
            },
        )
        if message is not None:
            details.append(f"message-sent: {message.subject}")
        monitoring_logging.log_info(f"Finished task '{task.name}'.")
        return TaskExecutionReport(task=task, status=status, details=details, warnings=warnings)

    def emit_message(
        self,
        *,
        subject: str,
        body: str,
        recipients: Sequence[str] | None = None,
        metadata: dict[str, object] | None = None,
    ) -> AgentMessage | None:
        """Publish a message to the communication hub if one is configured."""

        if self.communication_hub is None:
            return None
        message = self.communication_hub.send(
            sender=self.agent_type,
            subject=subject,
            body=body,
            recipients=recipients,
            metadata=dict(metadata or {}),
        )
        monitoring_logging.log_info(
            "Communication emitted: " + str(message.to_dict())
        )
        return message

    def _collect_instructions(self) -> List[AgentMessage]:
        """Fetch messages addressed to this agent before task execution."""

        if self.communication_hub is None:
            return []
        instructions = [
            message
            for message in self.communication_hub.messages_for(self.agent_type)
            if message.subject.startswith("agent-start::")
            or message.subject.startswith("orchestration-start")
        ]
        for message in instructions:
            monitoring_logging.log_info(
                "Instruction received: " + str(message.to_dict())
            )
        return instructions


__all__ = [
    "AgentExecutionError",
    "AgentRunReport",
    "BaseAgent",
    "TaskExecutionReport",
]
