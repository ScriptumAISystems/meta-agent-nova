"""Utilities for rendering orchestration reports into shareable documents."""

from __future__ import annotations

from ..system.orchestrator import OrchestrationReport


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
