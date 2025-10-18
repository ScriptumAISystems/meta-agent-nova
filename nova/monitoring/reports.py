"""Utilities for rendering orchestration reports into shareable documents."""

from __future__ import annotations

from typing import Dict

from ..system.orchestrator import OrchestrationReport


def _derive_phase_metrics(report: OrchestrationReport) -> Dict[str, Dict[str, int]]:
    metrics: Dict[str, Dict[str, int]] = {}
    if not report.execution_plan or not report.execution_plan.phases:
        return metrics
    for phase in report.execution_plan.phases:
        agents = {agent for agent in phase.agents}
        total = 0
        completed = 0
        for agent_report in report.agent_reports:
            if agent_report.agent_type in agents:
                total += len(agent_report.task_reports)
                completed += sum(
                    1 for task in agent_report.task_reports if task.status == "completed"
                )
        metrics[phase.name] = {"completed": completed, "total": total}
    return metrics


def build_markdown_test_report(
    report: OrchestrationReport,
    *,
    title: str = "Nova Integration Test Report",
) -> str:
    """Create a Markdown report describing orchestration results."""

    lines: list[str] = [f"# {title}"]
    lines.append("")
    lines.append(f"* Overall status: {'success' if report.success else 'issues detected'}")
    lines.append(f"* Execution mode: {report.execution_mode}")
    lines.append("")
    if report.execution_plan and report.execution_plan.phases:
        lines.append("## Execution Plan")
        for phase in report.execution_plan.phases:
            lines.append(f"- **{phase.name}**: {phase.goal}")
            lines.append("  - Agents: " + ", ".join(phase.agents))
        lines.append("")
    lines.append("## Phase Metrics")
    phase_metrics = report.phase_metrics or _derive_phase_metrics(report)
    if phase_metrics:
        for phase_name, values in phase_metrics.items():
            completed = values.get("completed") or values.get("completed_tasks") or 0
            total = values.get("total") or values.get("total_tasks") or 0
            percent = int(round((completed / total) * 100)) if total else 0
            lines.append(
                f"- **{phase_name}**: {completed}/{total} completed ({percent}%)"
            )
    else:
        lines.append("- No phase metrics available.")
    lines.append("")
    lines.append("## Memory Usage")
    memory_usage = getattr(report, "memory_usage", None)
    if isinstance(memory_usage, dict):
        if memory_usage:
            for key, value in memory_usage.items():
                lines.append(f"- {key}: {value}")
        else:
            lines.append("- Memory usage data unavailable.")
    else:
        lines.append("- Memory usage data unavailable.")
    lines.append("")
    lines.append("## Governance Verdicts")
    governance_entries = getattr(report, "governance_verdicts", None)
    if governance_entries:
        for entry in governance_entries:
            if not isinstance(entry, dict):
                continue
            action = entry.get("action", "unknown")
            verdict = entry.get("verdict", "UNKNOWN")
            rationale = entry.get("rationale") or ""
            details = entry.get("details")
            detail_text = ""
            if isinstance(details, dict) and details:
                detail_text = f" – details: {', '.join(f'{k}={v}' for k, v in details.items())}"
            rationale_text = f" ({rationale})" if rationale else ""
            lines.append(f"- **{action}** → {verdict}{rationale_text}{detail_text}")
    else:
        lines.append("- No governance decisions recorded.")
    lines.append("")
    lines.append("## Agent Outcomes")
    if not report.agent_reports:
        lines.append("- No agents executed.")
    for agent_report in report.agent_reports:
        lines.append(f"- **{agent_report.agent_type}** → {'success' if agent_report.success else 'issues'}")
        if agent_report.pre_run_messages:
            lines.append("  - Instructions: " + ", ".join(message.subject for message in agent_report.pre_run_messages))
        for task_report in agent_report.task_reports:
            lines.append(
                f"  - Task `{task_report.task.name}`: {task_report.status}"
            )
            if task_report.warnings:
                lines.append("    - Warnings: " + ", ".join(task_report.warnings))
    lines.append("")
    lines.append("## Communication Summary")
    if not report.communication_log:
        lines.append("- No messages recorded.")
    else:
        for message in report.communication_log:
            lines.append(
                "- "
                + message.sender
                + " → "
                + ", ".join(message.recipients)
                + f": {message.subject}"
            )
    return "\n".join(lines).strip()


def extract_failed_tasks(report: OrchestrationReport) -> list[tuple[str, str]]:
    """Return a list of ``(agent_type, task_name)`` pairs that were not completed."""

    failures: list[tuple[str, str]] = []
    for agent_report in report.agent_reports:
        for task_report in agent_report.task_reports:
            if task_report.status != "completed":
                failures.append((agent_report.agent_type, task_report.task.name))
    return failures


def summarise_agent_metrics(report: OrchestrationReport) -> dict[str, int]:
    """Aggregate the number of tasks executed per agent."""

    return {
        agent_report.agent_type: len(agent_report.task_reports)
        for agent_report in report.agent_reports
    }


__all__ = [
    "build_markdown_test_report",
    "extract_failed_tasks",
    "summarise_agent_metrics",
]
