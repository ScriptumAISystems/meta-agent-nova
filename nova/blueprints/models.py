"""Domain models for Nova agent blueprints.

The lightweight data structures defined in this module provide a typed
representation of blueprint specifications that can be consumed by the
agents and orchestration layers.  Keeping the models in a dedicated
module avoids circular imports between the blueprint generator and the
agent implementations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List


@dataclass(slots=True)
class AgentTaskSpec:
    """Describe a single task that belongs to an agent blueprint.

    Attributes
    ----------
    name:
        Short identifier of the task.
    goal:
        High level description of the intended outcome.
    steps:
        Ordered list of actionable steps the agent should execute.
    outputs:
        Human readable summary of the expected artefacts or side effects.
    """

    name: str
    goal: str
    steps: List[str]
    outputs: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialise the task specification into a JSON compatible dict."""

        return {
            "name": self.name,
            "goal": self.goal,
            "steps": list(self.steps),
            "outputs": list(self.outputs),
        }


@dataclass(slots=True)
class AgentBlueprint:
    """Collection of tasks for an agent role."""

    agent_type: str
    description: str
    tasks: List[AgentTaskSpec] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.agent_type = self.agent_type.lower()

    def to_dict(self) -> dict:
        """Serialise the blueprint and its tasks for logging or storage."""

        return {
            "agent_type": self.agent_type,
            "description": self.description,
            "tasks": [task.to_dict() for task in self.tasks],
        }

    @classmethod
    def from_dict(cls, payload: dict) -> "AgentBlueprint":
        """Create a blueprint instance from a dictionary payload."""

        tasks_payload = payload.get("tasks", [])
        tasks = [
            AgentTaskSpec(
                name=task.get("name", "task"),
                goal=task.get("goal", ""),
                steps=list(task.get("steps", [])),
                outputs=list(task.get("outputs", [])),
            )
            for task in tasks_payload
        ]
        return cls(
            agent_type=payload.get("agent_type", "unknown"),
            description=payload.get("description", ""),
            tasks=tasks,
        )


def build_blueprint(agent_type: str, description: str, tasks: Iterable[AgentTaskSpec]) -> AgentBlueprint:
    """Factory helper used by the blueprint generator."""

    return AgentBlueprint(agent_type=agent_type, description=description, tasks=list(tasks))


__all__ = [
    "AgentBlueprint",
    "AgentTaskSpec",
    "build_blueprint",
]
