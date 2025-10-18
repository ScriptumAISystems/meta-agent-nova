"""Task orchestration for Meta-Agent Nova."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List

import sys

try:  # pragma: no cover - optional on some platforms
    import resource
except Exception:  # pragma: no cover - optional dependency missing
    resource = None  # type: ignore[assignment]

from ..agents.base import AgentRunReport
from ..agents.registry import get_agent_class, list_agent_types
from ..blueprints.generator import create_blueprint
from ..blueprints.models import AgentBlueprint
from ..system.communication import AgentMessage, CommunicationHub
from ..system.mission import ExecutionPhase, ExecutionPlan, build_default_plan
from ..monitoring.alerts import notify_info, notify_warning
from ..monitoring.logging import log_error, log_info


@dataclass(slots=True)
class OrchestrationReport:
    """Summary describing the result of an orchestration run."""

    agent_reports: List[AgentRunReport]
    communication_log: List[AgentMessage]
    execution_mode: str = "sequential"
    execution_plan: ExecutionPlan | None = None
    phase_metrics: Dict[str, Dict[str, int]] | None = None
    memory_usage: Dict[str, Any] | None = None
    governance_verdicts: List[Dict[str, Any]] | None = None

    @property
    def success(self) -> bool:
        return all(report.success for report in self.agent_reports)

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "agents": [report.to_dict() for report in self.agent_reports],
            "messages": [message.to_dict() for message in self.communication_log],
            "execution_mode": self.execution_mode,
            "execution_plan": self.execution_plan.to_dict()
            if self.execution_plan
            else None,
            "phase_metrics": self.phase_metrics,
            "memory_usage": dict(self.memory_usage) if self.memory_usage is not None else None,
            "governance_verdicts": list(self.governance_verdicts)
            if self.governance_verdicts
            else [],
        }

    def to_markdown(self) -> str:
        """Render the orchestration summary as a Markdown report."""

        lines: List[str] = [
            "# Orchestration Report",
            "",
            f"* Overall status: {'success' if self.success else 'issues detected'}",
            f"* Execution mode: {self.execution_mode}",
            "",
        ]
        if self.execution_plan and self.execution_plan.phases:
            lines.append("## Execution Plan")
            for phase in self.execution_plan.phases:
                lines.append(f"- **{phase.name}**: {phase.goal}")
                lines.append("  - Agents: " + ", ".join(phase.agents))
            lines.append("")
        metrics = self.phase_metrics or {}
        if not metrics and self.execution_plan and self.execution_plan.phases:
            metrics = {}
            for phase in self.execution_plan.phases:
                agents = {agent for agent in phase.agents}
                total = 0
                completed = 0
                for report in self.agent_reports:
                    if report.agent_type in agents:
                        total += len(report.task_reports)
                        completed += sum(
                            1 for task in report.task_reports if task.status == "completed"
                        )
                metrics[phase.name] = {"completed": completed, "total": total}
        lines.append("## Phase Metrics")
        if metrics:
            for name, data in metrics.items():
                completed = data.get("completed") or data.get("completed_tasks") or 0
                total = data.get("total") or data.get("total_tasks") or 0
                percent = int(round((completed / total) * 100)) if total else 0
                lines.append(f"- **{name}**: {completed}/{total} completed ({percent}%)")
        else:
            lines.append("- No phase metrics available.")
        lines.append("")
        lines.append("## Memory Usage")
        memory_usage = self.memory_usage or {}
        if memory_usage:
            for key, value in memory_usage.items():
                lines.append(f"- {key}: {value}")
        else:
            lines.append("- Memory usage data unavailable.")
        lines.append("")
        lines.append("## Governance Verdicts")
        decisions = self.governance_verdicts or []
        if decisions:
            for decision in decisions:
                action = decision.get("action", "unknown") if isinstance(decision, dict) else "unknown"
                verdict = decision.get("verdict", "UNKNOWN") if isinstance(decision, dict) else str(decision)
                rationale = ""
                details = ""
                if isinstance(decision, dict):
                    rationale = decision.get("rationale") or ""
                    extra = decision.get("details")
                    if isinstance(extra, dict) and extra:
                        details = ", ".join(f"{k}={v}" for k, v in extra.items())
                rationale_text = f" ({rationale})" if rationale else ""
                details_text = f" – details: {details}" if details else ""
                lines.append(f"- **{action}** → {verdict}{rationale_text}{details_text}")
        else:
            lines.append("- No governance decisions recorded.")
        lines.append("")
        lines.append("## Agent Runs")
        lines.append("")
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
        execution_plan: ExecutionPlan | None = None,
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
        base_plan = execution_plan or build_default_plan()
        self.execution_plan = base_plan.filtered(self.agent_types)
        self.agent_types = list(self.execution_plan.iter_agents())

    def _get_blueprint(self, agent_type: str) -> AgentBlueprint:
        blueprint = self._blueprint_cache.get(agent_type)
        if blueprint is None:
            blueprint = create_blueprint(agent_type)
            self._blueprint_cache[agent_type] = blueprint
        return blueprint

    def _announce_phase_start(self, phase: ExecutionPhase) -> None:
        if not phase.agents:
            return
        self.communication_hub.broadcast(
            sender="orchestrator",
            subject=f"phase-start::{phase.name}",
            body=phase.goal,
            metadata={"agents": list(phase.agents)},
        )
        for agent_type in phase.agents:
            blueprint = self._get_blueprint(agent_type)
            dependencies = self.execution_plan.dependencies_for(agent_type)
            self.communication_hub.send(
                sender="orchestrator",
                subject=f"agent-start::{agent_type}",
                body=(
                    f"Agent {agent_type} requested to begin execution during phase {phase.name}."
                ),
                recipients=(agent_type,),
                metadata={
                    "tasks": len(blueprint.tasks),
                    "phase": phase.name,
                    "depends_on": list(dependencies),
                },
            )

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

    def _sequential_execution(self, agent_sequence: Iterable[str]) -> List[AgentRunReport]:
        reports: List[AgentRunReport] = []
        for agent_type in agent_sequence:
            report = self._run_agent(agent_type)
            if report is not None:
                reports.append(report)
        return reports

    def _parallel_execution(self, agent_sequence: Iterable[str]) -> List[AgentRunReport]:
        reports: List[AgentRunReport] = []
        agent_list = list(agent_sequence)
        if not agent_list:
            return reports
        workers = self.max_workers or len(agent_list)
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(self._run_agent, agent): agent for agent in agent_list}
            for future in as_completed(futures):
                report = future.result()
                if report is not None:
                    reports.append(report)
        reports.sort(key=lambda item: agent_list.index(item.agent_type))
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
            metadata={
                "agents": list(self.agent_types),
                "mode": mode,
                "plan": self.execution_plan.to_dict()
                if self.execution_plan
                else None,
            },
        )
        reports: List[AgentRunReport] = []
        phases = self.execution_plan.phases if self.execution_plan else ()
        plan_for_report: ExecutionPlan | None = self.execution_plan
        if not phases and self.agent_types:
            phases = (
                ExecutionPhase(
                    name="ad-hoc",
                    goal="Default execution phase for unplanned agents.",
                    agents=tuple(self.agent_types),
                ),
            )
            plan_for_report = ExecutionPlan(phases)

        for phase in phases:
            if not phase.agents:
                continue
            self._announce_phase_start(phase)
            if mode == "parallel":
                reports.extend(self._parallel_execution(phase.agents))
            else:
                reports.extend(self._sequential_execution(phase.agents))

        phase_metrics: Dict[str, Dict[str, int]] = {}
        if plan_for_report and plan_for_report.phases:
            for phase in plan_for_report.phases:
                agents = {agent for agent in phase.agents}
                total_tasks = 0
                completed_tasks = 0
                for agent_report in reports:
                    if agent_report.agent_type in agents:
                        total_tasks += len(agent_report.task_reports)
                        completed_tasks += sum(
                            1
                            for task_report in agent_report.task_reports
                            if task_report.status == "completed"
                        )
                phase_metrics[phase.name] = {
                    "completed": completed_tasks,
                    "total": total_tasks,
                }
        memory_stats: Dict[str, Any] = {}
        if resource is not None:
            usage = resource.getrusage(resource.RUSAGE_SELF)
            peak_rss = getattr(usage, "ru_maxrss", 0)
            if peak_rss:
                if sys.platform == "darwin":
                    rss_mb = round(peak_rss / (1024 * 1024), 2)
                else:
                    rss_mb = round(peak_rss / 1024, 2)
                memory_stats["peak_rss_mb"] = rss_mb
        if reports:
            memory_stats.setdefault("agent_reports", len(reports))
        governance_records: List[Dict[str, Any]] = []
        for message in self.communication_hub.messages:
            metadata = message.metadata or {}
            if not isinstance(metadata, dict):
                continue
            if message.subject.startswith("governance"):
                governance_records.append(
                    {
                        "action": metadata.get("action", message.subject),
                        "verdict": metadata.get("verdict", metadata.get("decision", "UNKNOWN")),
                        "rationale": metadata.get("rationale", ""),
                        "details": metadata.get("details", {}),
                    }
                )
        orchestration_report = OrchestrationReport(
            agent_reports=reports,
            communication_log=list(self.communication_hub.messages),
            execution_mode=mode,
            execution_plan=plan_for_report,
            phase_metrics=phase_metrics or None,
            memory_usage=memory_stats or None,
            governance_verdicts=governance_records,
        )
        if orchestration_report.success:
            notify_info("All agents completed successfully.")
        else:
            notify_warning("One or more agents reported issues.")
        return orchestration_report


__all__ = ["Orchestrator", "OrchestrationReport"]
