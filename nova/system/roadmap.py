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


def _normalise_phase_name(name: str) -> str:
    """Return a case-insensitive key for matching phase names."""

    return name.strip().lower().replace(" ", "-")


def build_phase_roadmap(
    tasks: Sequence[AgentTask],
    plan: ExecutionPlan | None = None,
    *,
    phase_filters: Iterable[str] | None = None,
) -> str:
    """Render a Markdown roadmap outlining the remaining steps per phase."""

    effective_plan = plan or build_default_plan()

    filter_names = [name.strip() for name in phase_filters or [] if name and name.strip()]
    normalised_filters = {
        _normalise_phase_name(name) for name in filter_names
    } or None

    if normalised_filters is None:
        selected_phases = effective_plan.phases
    else:
        selected_phases = tuple(
            phase
            for phase in effective_plan.phases
            if _normalise_phase_name(phase.name) in normalised_filters
        )

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

    if filter_names:
        lines.append("*Gefiltert nach Phasen:* " + ", ".join(filter_names))
        lines.append("")

    if not effective_plan.phases:
        lines.append("Keine Phasen definiert.")
        return "\n".join(lines).strip()

    if normalised_filters is not None and not selected_phases:
        lines.append(
            "*Hinweis:* Keine der angeforderten Phasen wurden im Ausführungsplan gefunden."
        )
        return "\n".join(lines).strip()

    for phase in selected_phases:
        lines.extend(_render_phase_section(phase, tasks))

    return "\n".join(lines).rstrip()


def _pending_tasks_by_agent(tasks: Sequence[AgentTask]) -> tuple[dict[str, list[AgentTask]], dict[str, tuple[str, str | None]]]:
    pending: dict[str, list[AgentTask]] = {}
    metadata: dict[str, tuple[str, str | None]] = {}
    for task in tasks:
        metadata.setdefault(task.agent_identifier, (task.agent_display_name, task.agent_role))
        if is_task_complete(task.status):
            continue
        pending.setdefault(task.agent_identifier, []).append(task)
    return pending, metadata


def _render_agent_next_steps(
    agent_id: str,
    tasks: Sequence[AgentTask],
    metadata: dict[str, tuple[str, str | None]],
    limit: int | None,
) -> list[str]:
    display_name, role = metadata.get(agent_id, (agent_id.title(), None))
    block: list[str] = [f"### {display_name}"]
    if role:
        block.append(f"*Rolle:* {role}")

    if limit is None:
        selected = list(tasks)
    else:
        limit = max(limit, 0)
        selected = list(tasks[:limit])

    for task in selected:
        block.append(f"- {task.description} (Status: {task.status})")

    remaining = len(tasks) - len(selected)
    if remaining > 0:
        plural = "n" if remaining != 1 else ""
        block.append(f"- … {remaining} weitere Aufgabe{plural} offen.")

    block.append("")
    return block


def build_next_steps_summary(
    tasks: Sequence[AgentTask],
    plan: ExecutionPlan | None = None,
    *,
    limit_per_agent: int = 1,
) -> str:
    """Return a Markdown summary highlighting the next steps per agent."""

    pending, metadata = _pending_tasks_by_agent(tasks)
    if not pending:
        return "# Nova Nächste Schritte\n\nAlle Aufgaben abgeschlossen. ✅"

    effective_plan = plan or build_default_plan()
    limit = None if limit_per_agent <= 0 else limit_per_agent

    total_pending = sum(len(agent_tasks) for agent_tasks in pending.values())
    limit_label = "alle" if limit is None else str(limit)

    lines: list[str] = [
        "# Nova Nächste Schritte",
        "",
        f"- Offene Aufgaben gesamt: {total_pending}",
        f"- Angezeigte Schritte pro Agent: {limit_label}",
        "",
    ]

    seen_agents: set[str] = set()
    for phase in effective_plan.phases:
        phase_agents = [agent for agent in phase.agents if agent in pending]
        if not phase_agents:
            continue

        lines.append(f"## {phase.name.title()}")
        lines.append(phase.goal)
        lines.append("")

        for agent_id in phase_agents:
            lines.extend(
                _render_agent_next_steps(agent_id, pending[agent_id], metadata, limit)
            )
            seen_agents.add(agent_id)

    remaining_agents = [agent for agent in pending if agent not in seen_agents]
    if remaining_agents:
        lines.append("## Ad-Hoc")
        lines.append("Aufgaben ohne Phasenzuordnung im aktuellen Ausführungsplan.")
        lines.append("")
        for agent_id in remaining_agents:
            lines.extend(
                _render_agent_next_steps(agent_id, pending[agent_id], metadata, limit)
            )

    return "\n".join(lines).rstrip()


def build_global_step_plan(
    tasks: Sequence[AgentTask],
    plan: ExecutionPlan | None = None,
    *,
    phase_filters: Iterable[str] | None = None,
) -> str:
    """Render a numbered, phase-ordered plan covering all tasks."""

    if not tasks:
        return "# Nova Schritt-für-Schritt Plan\n\nKeine Aufgaben gefunden."

    effective_plan = plan or build_default_plan()

    filter_names = [name.strip() for name in phase_filters or [] if name and name.strip()]
    normalised_filters = {
        _normalise_phase_name(name) for name in filter_names
    } or None

    if normalised_filters is None:
        selected_phases = effective_plan.phases
    else:
        selected_phases = tuple(
            phase
            for phase in effective_plan.phases
            if _normalise_phase_name(phase.name) in normalised_filters
        )

    total_tasks = len(tasks)
    completed_tasks = sum(1 for task in tasks if is_task_complete(task.status))

    lines: list[str] = [
        "# Nova Schritt-für-Schritt Plan",
        "",
        f"- Gesamtaufgaben: {total_tasks}",
        f"- Abgeschlossen: {completed_tasks}",
        f"- Offen: {total_tasks - completed_tasks}",
        "",
    ]

    if filter_names:
        lines.append("*Gefiltert nach Phasen:* " + ", ".join(filter_names))
        lines.append("")

    if not effective_plan.phases:
        lines.append("Keine Phasen definiert.")
        return "\n".join(lines).strip()

    if normalised_filters is not None and not selected_phases:
        lines.append("*Hinweis:* Keine der angeforderten Phasen wurden im Ausführungsplan gefunden.")
        return "\n".join(lines).strip()

    tasks_by_agent: dict[str, list[AgentTask]] = {}
    metadata: dict[str, tuple[str, str | None]] = {}
    for task in tasks:
        tasks_by_agent.setdefault(task.agent_identifier, []).append(task)
        metadata.setdefault(
            task.agent_identifier,
            (task.agent_display_name, task.agent_role),
        )

    for agent_tasks in tasks_by_agent.values():
        agent_tasks.sort(key=lambda task: task.description.lower())

    step = 1
    seen_agents: set[str] = set()
    selected_phase_agent_ids: set[str] = {
        agent for phase in selected_phases for agent in phase.agents
    }
    all_plan_agents: set[str] = {
        agent for phase in effective_plan.phases for agent in phase.agents
    }

    for phase in selected_phases:
        phase_agent_ids = [agent for agent in phase.agents if agent in tasks_by_agent]
        if not phase_agent_ids:
            continue

        lines.append(f"## {phase.name.title()}")
        lines.append(phase.goal)
        lines.append("")

        for agent_id in phase_agent_ids:
            display_name, role = metadata.get(agent_id, (agent_id.title(), None))
            lines.append(f"### {display_name}")
            if role:
                lines.append(f"*Rolle:* {role}")

            for task in tasks_by_agent[agent_id]:
                checkbox = "x" if is_task_complete(task.status) else " "
                lines.append(
                    f"{step}. [{checkbox}] {task.description} (Status: {task.status})"
                )
                step += 1

            lines.append("")
            seen_agents.add(agent_id)

    remaining_agents: list[str] = []
    for agent_id in sorted(tasks_by_agent):
        if agent_id in seen_agents:
            continue
        if agent_id in selected_phase_agent_ids:
            continue
        if normalised_filters is not None and agent_id in all_plan_agents:
            # Skip agents that belong to filtered-out phases.
            continue
        remaining_agents.append(agent_id)

    if remaining_agents:
        lines.append("## Ad-Hoc")
        lines.append("Aufgaben ohne Zuordnung in den ausgewählten Phasen.")
        lines.append("")

        for agent_id in remaining_agents:
            display_name, role = metadata.get(agent_id, (agent_id.title(), None))
            lines.append(f"### {display_name}")
            if role:
                lines.append(f"*Rolle:* {role}")

            for task in tasks_by_agent[agent_id]:
                checkbox = "x" if is_task_complete(task.status) else " "
                lines.append(
                    f"{step}. [{checkbox}] {task.description} (Status: {task.status})"
                )
                step += 1

            lines.append("")

    return "\n".join(lines).rstrip()


__all__ = [
    "build_phase_roadmap",
    "build_next_steps_summary",
    "build_global_step_plan",
]

