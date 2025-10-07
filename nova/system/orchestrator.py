"""Task orchestration for Meta-Agent Nova."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from ..agents.base import AgentRunReport
from ..agents.registry import get_agent_class, list_agent_types
from ..blueprints.generator import create_blueprint
from ..monitoring.alerts import notify_info, notify_warning
from ..monitoring.logging import log_error, log_info


@dataclass(slots=True)
class OrchestrationReport:
    """Summary describing the result of an orchestration run."""

    agent_reports: List[AgentRunReport]

    @property
    def success(self) -> bool:
        return all(report.success for report in self.agent_reports)

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "agents": [report.to_dict() for report in self.agent_reports],
        }


class Orchestrator:
    """Coordinates blueprint execution across registered agents."""

    def __init__(self, agent_types: Iterable[str] | None = None):
        self.agent_types = list(agent_types) if agent_types else list_agent_types()

    def execute(self) -> OrchestrationReport:
        log_info(
            "Starting orchestration run for agents: " + ", ".join(self.agent_types)
        )
        reports: List[AgentRunReport] = []
        for agent_type in self.agent_types:
            agent_cls = get_agent_class(agent_type)
            if not agent_cls:
                notify_warning(f"No agent registered for type '{agent_type}'.")
                continue
            blueprint = create_blueprint(agent_type)
            if not blueprint.tasks:
                notify_warning(
                    f"Blueprint for agent '{agent_type}' defines no tasks. Skipping execution."
                )
                continue
            agent = agent_cls(blueprint)
            log_info(f"Executing agent '{agent_type}' with {len(blueprint.tasks)} tasks.")
            try:
                report = agent.execute()
            except Exception as exc:  # pragma: no cover - defensive logging
                log_error(f"Agent '{agent_type}' failed: {exc}")
                raise
            reports.append(report)

        orchestration_report = OrchestrationReport(agent_reports=reports)
        if orchestration_report.success:
            notify_info("All agents completed successfully.")
        else:
            notify_warning("One or more agents reported issues.")
        return orchestration_report


__all__ = ["Orchestrator", "OrchestrationReport"]
