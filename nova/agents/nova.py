"""Nova chief agent implementation."""

from __future__ import annotations

from .base import BaseAgent


class NovaAgent(BaseAgent):
    """Coordinates infrastructure preparation and governance tasks."""

    agent_type = "nova"

    def execute_task(self, task):  # type: ignore[override]
        report = super().execute_task(task)
        if task.name == "infrastructure-audit":
            report.details.append("audit: hardware baseline documented")
        elif task.name == "container-platform":
            report.details.append("containers: docker and kubernetes validated")
        elif task.name == "secure-remote-access":
            report.details.append("remote-access: vpn templates staged")
        elif task.name == "security-audit":
            report.details.append("security: firewall and opa review logged")
        elif task.name == "backup-recovery":
            report.details.append("resilience: backup runbook distributed")
        return report


__all__ = ["NovaAgent"]
