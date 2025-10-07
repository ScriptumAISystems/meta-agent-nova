"""Orion agent implementation."""

from __future__ import annotations

from .base import BaseAgent


class OrionAgent(BaseAgent):
    agent_type = "orion"

    def execute_task(self, task):  # type: ignore[override]
        report = super().execute_task(task)
        if task.name == "nemo-installation":
            report.details.append("nemo: compatibility matrix validated")
        elif task.name == "finetuning-protocol":
            report.details.append("finetuning: evaluation metrics defined")
        return report


__all__ = ["OrionAgent"]
