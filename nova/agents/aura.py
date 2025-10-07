"""Aura agent implementation."""

from __future__ import annotations

from .base import BaseAgent


class AuraAgent(BaseAgent):
    """Simulated implementation of the observability specialist."""

    agent_type = "aura"

    def execute_task(self, task):  # type: ignore[override]
        report = super().execute_task(task)
        if task.name == "install-grafana":
            report.details.append("grafana-configured: dashboards registered")
        elif task.name == "emotional-feedback-visualisation":
            report.details.append("sentiment-report: generated weekly digest")
        return report


__all__ = ["AuraAgent"]
