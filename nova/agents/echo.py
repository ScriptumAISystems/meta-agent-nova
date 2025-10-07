"""Echo agent implementation."""

from __future__ import annotations

from .base import BaseAgent


class EchoAgent(BaseAgent):
    agent_type = "echo"

    def execute_task(self, task):  # type: ignore[override]
        report = super().execute_task(task)
        if task.name == "ace-toolkit-setup":
            report.details.append("ace-toolkit: readiness checklist compiled")
        elif task.name == "teams-integration":
            report.details.append("teams-manifest: draft stored")
        return report


__all__ = ["EchoAgent"]
