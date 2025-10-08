"""Utilities for rendering aggregated progress reports."""

from __future__ import annotations

from typing import Sequence

from .tasks import AgentTask, group_tasks_by_agent, is_task_complete


def _percentage(completed: int, total: int) -> int:
    """Return the completion percentage for ``completed`` out of ``total``."""

    if total <= 0:
        return 0
    return int(round((completed / total) * 100))


def _render_pending_tasks(
    tasks: Sequence[AgentTask], pending_limit: int
) -> list[str]:
    """Render a bullet list of pending tasks constrained by ``pending_limit``."""

    pending = [task for task in tasks if not is_task_complete(task.status)]
    if not pending:
        return ["Alle Aufgaben abgeschlossen. ✅"]

    lines = ["### Nächste Schritte"]
    if pending_limit <= 0:
        selected = list(pending)
    else:
        selected = list(pending[:pending_limit])

    for task in selected:
        lines.append(f"- [ ] {task.description} (Status: {task.status})")

    remaining = len(pending) - len(selected)
    if remaining > 0:
        plural = "n" if remaining != 1 else ""
        lines.append(f"- … {remaining} weitere Aufgabe{plural} offen.")

    return lines


def build_progress_report(
    tasks: Sequence[AgentTask], *, pending_limit: int = 3
) -> str:
    """Return a Markdown progress snapshot for ``tasks``."""

    if not tasks:
        return "# Nova Fortschrittsbericht\n\nKeine Aufgaben gefunden."

    total = len(tasks)
    completed = sum(1 for task in tasks if is_task_complete(task.status))
    percentage = _percentage(completed, total)

    lines: list[str] = [
        "# Nova Fortschrittsbericht",
        "",
        f"- Gesamtaufgaben: {total}",
        f"- Abgeschlossen: {completed}",
        f"- Fortschritt: {percentage}%",
        "",
    ]

    grouped = group_tasks_by_agent(tasks)
    for display_name, agent_tasks in grouped.items():
        lines.append(f"## {display_name}")
        role = agent_tasks[0].agent_role
        if role:
            lines.append(f"*Rolle:* {role}")

        agent_total = len(agent_tasks)
        agent_completed = sum(
            1 for task in agent_tasks if is_task_complete(task.status)
        )
        agent_percentage = _percentage(agent_completed, agent_total)

        lines.append(f"- Aufgaben: {agent_total}")
        lines.append(f"- Abgeschlossen: {agent_completed}")
        lines.append(f"- Fortschritt: {agent_percentage}%")
        lines.append("")
        lines.extend(_render_pending_tasks(agent_tasks, pending_limit))
        lines.append("")

    return "\n".join(lines).rstrip()


__all__ = ["build_progress_report"]

