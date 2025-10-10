"""Utilities for loading and summarising agent task overviews.

The Nova project ships a CSV file that lists the outstanding work items for
each specialist agent.  This module provides helpers to parse that overview,
group the tasks by agent and render a concise markdown summary that can be
surfaced through the command line interface.
"""

from __future__ import annotations

from collections import Counter, defaultdict
import csv
from dataclasses import dataclass
import os
from pathlib import Path
from typing import Iterable, Sequence

from collections.abc import Iterable as IterableABC


@dataclass(frozen=True)
class AgentTask:
    """Representation of a single agent task entry."""

    agent_identifier: str
    agent_display_name: str
    agent_role: str | None
    description: str
    status: str


_DEFAULT_TASK_CSV = Path(__file__).resolve().parents[2] / "Agenten_Aufgaben_Uebersicht.csv"

_COMPLETED_STATUSES = {
    "abgeschlossen",
    "completed",
    "done",
    "fertig",
}


def is_task_complete(status: str) -> bool:
    """Return ``True`` if ``status`` represents a completed task."""

    return status.strip().lower() in _COMPLETED_STATUSES


def resolve_task_csv_path(csv_path: Path | str | None = None) -> Path:
    """Return the effective CSV path, considering overrides."""

    if csv_path is not None:
        return Path(csv_path)
    env_path = os.environ.get("NOVA_TASK_CSV")
    if env_path:
        return Path(env_path)
    return _DEFAULT_TASK_CSV


def load_agent_tasks(csv_path: Path | str | None = None) -> list[AgentTask]:
    """Load agent tasks from the configured CSV file."""

    path = resolve_task_csv_path(csv_path)
    if not path.exists():
        raise FileNotFoundError(path)

    tasks: list[AgentTask] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            raw_name = (row.get("Agenten-Name") or "").strip()
            description = (row.get("Aufgabe") or "").strip()
            status = (row.get("Status") or "").strip() or "Unbekannt"

            if not raw_name or not description:
                # Skip incomplete rows instead of failing hard.
                continue

            display_name = raw_name
            role: str | None = None
            identifier = raw_name.lower()
            if "(" in raw_name and raw_name.endswith(")"):
                prefix, _, suffix = raw_name.partition("(")
                identifier = prefix.strip().lower()
                role = suffix[:-1].strip() or None
                display_name = f"{prefix.strip()} ({role})" if role else prefix.strip()
            identifier = identifier.replace(" agent", "").replace(" ", "-")

            tasks.append(
                AgentTask(
                    agent_identifier=identifier,
                    agent_display_name=display_name,
                    agent_role=role,
                    description=description,
                    status=status,
                )
            )

    return tasks


def _normalise_status_filters(
    status: str | Iterable[str] | None,
) -> set[str] | None:
    """Return a normalised set of status filters."""

    if status is None:
        return None

    if isinstance(status, str):
        raw_values: Iterable[str] = [status]
    elif isinstance(status, IterableABC):
        raw_values = status
    else:
        raw_values = [str(status)]

    filters = {
        part.strip().lower()
        for value in raw_values
        for part in str(value).replace(";", ",").split(",")
        if part.strip()
    }
    return filters or None


def filter_tasks(
    tasks: Sequence[AgentTask],
    agent_identifiers: Iterable[str] | None = None,
    status: str | Iterable[str] | None = None,
) -> list[AgentTask]:
    """Filter tasks by agent identifier and/or status label."""

    identifier_filter = (
        {normalise_agent_identifier(identifier) for identifier in agent_identifiers}
        if agent_identifiers
        else None
    )
    status_filter = _normalise_status_filters(status)

    filtered: list[AgentTask] = []
    for task in tasks:
        if identifier_filter and task.agent_identifier not in identifier_filter:
            continue
        if status_filter and task.status.strip().lower() not in status_filter:
            continue
        filtered.append(task)
    return filtered


def group_tasks_by_agent(tasks: Sequence[AgentTask]) -> dict[str, list[AgentTask]]:
    """Return tasks grouped by display name preserving alphabetical order."""

    grouped: dict[str, list[AgentTask]] = defaultdict(list)
    for task in tasks:
        grouped[task.agent_display_name].append(task)

    ordered: dict[str, list[AgentTask]] = {}
    for display_name in sorted(grouped, key=str.lower):
        ordered[display_name] = sorted(
            grouped[display_name], key=lambda task: task.description.lower()
        )
    return ordered


def build_markdown_task_overview(tasks: Sequence[AgentTask]) -> str:
    """Build a markdown overview report for ``tasks``."""

    if not tasks:
        return "# Nova Agent Task Overview\n\nKeine Aufgaben gefunden."

    counter = Counter(task.status for task in tasks)
    lines: list[str] = ["# Nova Agent Task Overview", ""]
    lines.append(f"- Total tasks: {len(tasks)}")
    for status_label in sorted(counter, key=str.lower):
        lines.append(f"- Status '{status_label}': {counter[status_label]}")

    grouped = group_tasks_by_agent(tasks)
    for display_name, agent_tasks in grouped.items():
        lines.append("")
        lines.append(f"## {display_name}")
        role = agent_tasks[0].agent_role
        if role:
            lines.append(f"*Rolle:* {role}")
        for task in agent_tasks:
            lines.append(f"- [{task.status}] {task.description}")

    return "\n".join(lines)


def build_stepwise_task_checklist(tasks: Sequence[AgentTask]) -> str:
    """Return a numbered, step-by-step checklist for ``tasks``."""

    if not tasks:
        return "# Nova Agent Task Checklist\n\nKeine Aufgaben gefunden."

    grouped = group_tasks_by_agent(tasks)
    lines: list[str] = ["# Nova Agent Task Checklist", "", f"- Gesamtanzahl Schritte: {len(tasks)}", ""]
    step = 1

    grouped_items = list(grouped.items())
    for index, (display_name, agent_tasks) in enumerate(grouped_items):
        lines.append(f"## {display_name}")
        role = agent_tasks[0].agent_role
        if role:
            lines.append(f"*Rolle:* {role}")
        for task in agent_tasks:
            checkbox = "x" if is_task_complete(task.status) else " "
            lines.append(
                f"{step}. [{checkbox}] {task.description} (Status: {task.status})"
            )
            step += 1
        if index < len(grouped_items) - 1:
            lines.append("")

    return "\n".join(lines)


def normalise_agent_identifier(identifier: str) -> str:
    """Normalise arbitrary agent identifier strings."""

    return identifier.strip().lower().replace(" agent", "").replace(" ", "-")


__all__ = [
    "AgentTask",
    "build_markdown_task_overview",
    "filter_tasks",
    "group_tasks_by_agent",
    "is_task_complete",
    "load_agent_tasks",
    "normalise_agent_identifier",
    "resolve_task_csv_path",
    "build_stepwise_task_checklist",
]
