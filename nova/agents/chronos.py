"""Chronos agent implementation."""

from __future__ import annotations

from .base import BaseAgent


class ChronosAgent(BaseAgent):
    agent_type = "chronos"

    def execute_task(self, task):  # type: ignore[override]
        report = super().execute_task(task)
        if task.name == "bootstrap-n8n":
            report.details.append("workflow-runner: compose manifest produced")
        elif task.name == "continuous-delivery":
            report.details.append("ci-cd: deployment artefacts registered")
        return report


__all__ = ["ChronosAgent"]
