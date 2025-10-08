"""Roadmap utilities for building step-by-step execution plans."""

from __future__ import annotations

from typing import Iterable, Sequence

from .mission import ExecutionPhase, ExecutionPlan, build_default_plan
from .tasks import (
    AgentTask,
    group_tasks_by_agent,
    is_task_complete,
    normalise_agent_identifier,
)


def _tasks_for_agents(
    tasks: Sequence[AgentTask], agents: Iterable[str]
) -> list[AgentTask]:
    """Return tasks assigned to the provided ``agents``."""

    agent_keys = {normalise_agent_identifier(agent) for agent in agents}
    if not agent_keys:
        return []
    return [task for task in tasks if task.agent_identifier in agent_keys]


def _render_pending_steps(pending: Sequence[AgentTask]) -> list[str]:
    if not pending:
        return []

    lines: list[str] = ["### Schritt-für-Schritt"]
    grouped = group_tasks_by_agent(pending)
    step = 1
    for display_name, agent_tasks in grouped.items():
        lines.append(f"#### {display_name}")
        role = agent_tasks[0].agent_role
        if role:
            lines.append(f"*Rolle:* {role}")
        for task in agent_tasks:
            lines.append(f"{step}. [ ] {task.description} (Status: {task.status})")
            step += 1
        lines.append("")
    return lines


def _render_phase_section(phase: ExecutionPhase, tasks: Sequence[AgentTask]) -> list[str]:
    section: list[str] = [
        f"## {phase.name.title()}",
        phase.goal,
    ]
    if phase.agents:
        section.append("*Agenten:* " + ", ".join(phase.agents))

    phase_tasks = _tasks_for_agents(tasks, phase.agents)
    total = len(phase_tasks)
    completed = sum(1 for task in phase_tasks if is_task_complete(task.status))
    percent = int(round((completed / total) * 100)) if total else 0
    section.append(f"*Fortschritt:* {completed}/{total} ({percent}%)")

    if not total:
        section.append("*Hinweis:* Für diese Phase sind noch keine Aufgaben im CSV hinterlegt.")
        section.append("")
        return section

    pending = [task for task in phase_tasks if not is_task_complete(task.status)]
    if not pending:
        section.append("Alle Schritte abgeschlossen. ✅")
        section.append("")
        return section

    section.append("")
    section.extend(_render_pending_steps(pending))
    return section


def build_phase_roadmap(
    tasks: Sequence[AgentTask], plan: ExecutionPlan | None = None
) -> str:
    """Render a Markdown roadmap outlining the remaining steps per phase."""

    effective_plan = plan or build_default_plan()

    total_tasks = len(tasks)
    completed_tasks = sum(1 for task in tasks if is_task_complete(task.status))

    lines: list[str] = [
        "# Nova Phasen-Roadmap",
        "",
        f"- Gesamtaufgaben: {total_tasks}",
        f"- Abgeschlossen: {completed_tasks}",
        f"- Offen: {total_tasks - completed_tasks}",
        "",
    ]

    if not effective_plan.phases:
        lines.append("Keine Phasen definiert.")
        return "\n".join(lines).strip()

    for phase in effective_plan.phases:
        lines.extend(_render_phase_section(phase, tasks))

    return "\n".join(lines).rstrip()


__all__ = ["build_phase_roadmap"]

