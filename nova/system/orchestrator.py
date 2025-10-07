"""Task orchestration for Meta-Agent Nova."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Iterable, List

from ..agents.base import AgentRunReport
from ..agents.registry import get_agent_class, list_agent_types
from ..blueprints.generator import create_blueprint
from ..blueprints.models import AgentBlueprint
from ..system.communication import AgentMessage, CommunicationHub
from ..monitoring.alerts import notify_info, notify_warning
from ..monitoring.logging import log_error, log_info


@dataclass(slots=True)
class OrchestrationReport:
    """Summary describing the result of an orchestration run."""

    agent_reports: List[AgentRunReport]
    communication_log: List[AgentMessage]
    execution_mode: str = "sequential"

    @property
    def success(self) -> bool:
        return all(report.success for report in self.agent_reports)

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "agents": [report.to_dict() for report in self.agent_reports],
            "messages": [message.to_dict() for message in self.communication_log],
            "execution_mode": self.execution_mode,
        }

    def to_markdown(self) -> str:
        """Render the orchestration summary as a Markdown report."""

        lines: List[str] = [
            "# Orchestration Report",
            "",
            f"* Overall status: {'success' if self.success else 'issues detected'}",
            f"* Execution mode: {self.execution_mode}",
            "",
            "## Agent Runs",
        ]
        for report in self.agent_reports:
            lines.append(report.to_markdown())
            lines.append("")
        lines.append("## Communication Log")
        if not self.communication_log:
            lines.append("- No messages recorded.")
        else:
            for message in self.communication_log:
                recipients = ", ".join(message.recipients)
                lines.append(
                    f"- `{message.sender}` → `{recipients}`: {message.subject}"
                )
        return "\n".join(lines).strip()


class Orchestrator:
    """Coordinates blueprint execution across registered agents."""

    def __init__(
        self,
        agent_types: Iterable[str] | None = None,
        *,
        communication_hub: CommunicationHub | None = None,
        execution_mode: str = "sequential",
        max_workers: int | None = None,
    ):
        available_agents = list_agent_types()
        if agent_types:
            normalised: List[str] = []
            for agent in agent_types:
                key = agent.lower()
                if key not in available_agents:
                    notify_warning(
                        f"Unknown agent '{agent}'. It will be ignored during orchestration."
                    )
                    continue
                normalised.append(key)
            self.agent_types = normalised
        else:
            self.agent_types = available_agents
        self.communication_hub = communication_hub or CommunicationHub()
        self.execution_mode = execution_mode
        self.max_workers = max_workers
        self._blueprint_cache: dict[str, AgentBlueprint] = {}

    def _get_blueprint(self, agent_type: str) -> AgentBlueprint:
        blueprint = self._blueprint_cache.get(agent_type)
        if blueprint is None:
            blueprint = create_blueprint(agent_type)
            self._blueprint_cache[agent_type] = blueprint
        return blueprint

    def _run_agent(self, agent_type: str) -> AgentRunReport | None:
        agent_cls = get_agent_class(agent_type)
        if not agent_cls:
            notify_warning(f"No agent registered for type '{agent_type}'.")
            return None
        blueprint = self._get_blueprint(agent_type)
        if not blueprint.tasks:
            notify_warning(
                f"Blueprint for agent '{agent_type}' defines no tasks. Skipping execution."
            )
            return None
        agent = agent_cls(blueprint, communication_hub=self.communication_hub)
        log_info(f"Executing agent '{agent_type}' with {len(blueprint.tasks)} tasks.")
        try:
            report = agent.execute()
        except Exception as exc:  # pragma: no cover - defensive logging
            log_error(f"Agent '{agent_type}' failed: {exc}")
            raise
        self.communication_hub.send(
            sender="orchestrator",
            subject=f"agent-run::{agent_type}",
            body=f"Agent {agent_type} completed execution.",
            recipients=(agent_type,),
            metadata={"tasks": len(report.task_reports), "success": report.success},
        )
        return report

    def _sequential_execution(self) -> List[AgentRunReport]:
        reports: List[AgentRunReport] = []
        for agent_type in self.agent_types:
            report = self._run_agent(agent_type)
            if report is not None:
                reports.append(report)
        return reports

    def _parallel_execution(self) -> List[AgentRunReport]:
        reports: List[AgentRunReport] = []
        if not self.agent_types:
            return reports
        workers = self.max_workers or len(self.agent_types)
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(self._run_agent, agent): agent for agent in self.agent_types}
            for future in as_completed(futures):
                report = future.result()
                if report is not None:
                    reports.append(report)
        reports.sort(key=lambda item: self.agent_types.index(item.agent_type))
        return reports

    def execute(self) -> OrchestrationReport:
        mode = self.execution_mode.lower()
        if mode not in {"sequential", "parallel"}:
            notify_warning(
                f"Unknown execution mode '{self.execution_mode}'. Falling back to sequential execution."
            )
            mode = "sequential"
        log_info(
            "Starting orchestration run for agents: " + ", ".join(self.agent_types)
        )
        self.communication_hub.broadcast(
            sender="orchestrator",
            subject="orchestration-start",
            body="Orchestration cycle initialised.",
            metadata={"agents": list(self.agent_types), "mode": mode},
        )
        for agent_type in self.agent_types:
            blueprint = self._get_blueprint(agent_type)
            self.communication_hub.send(
                sender="orchestrator",
                subject=f"agent-start::{agent_type}",
                body=f"Agent {agent_type} requested to begin execution.",
                recipients=(agent_type,),
                metadata={"tasks": len(blueprint.tasks)},
            )

        if mode == "parallel":
            reports = self._parallel_execution()
        else:
            reports = self._sequential_execution()

        orchestration_report = OrchestrationReport(
            agent_reports=reports,
            communication_log=list(self.communication_hub.messages),
            execution_mode=mode,
        )
        if orchestration_report.success:
            notify_info("All agents completed successfully.")
        else:
            notify_warning("One or more agents reported issues.")
        return orchestration_report


__all__ = ["Orchestrator", "OrchestrationReport"]
