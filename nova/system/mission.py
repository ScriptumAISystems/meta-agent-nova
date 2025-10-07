"""Execution planning utilities for the Nova orchestrator."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple


@dataclass(slots=True)
class ExecutionPhase:
    """Represents a logical phase within the orchestration lifecycle."""

    name: str
    goal: str
    agents: Tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "goal": self.goal,
            "agents": list(self.agents),
        }


@dataclass(slots=True)
class ExecutionPlan:
    """Sequence of :class:`ExecutionPhase` objects describing execution order."""

    phases: Tuple[ExecutionPhase, ...]

    def filtered(self, agent_types: Iterable[str]) -> "ExecutionPlan":
        """Return a plan containing only the requested ``agent_types``.

        Unknown agents are retained in an ``ad-hoc`` phase at the end of the
        plan so that orchestrator extensions can still execute them.
        """

        sequence: List[str] = [agent.lower() for agent in agent_types]
        if not sequence:
            return ExecutionPlan(())

        covered: set[str] = set()
        phases: List[ExecutionPhase] = []
        for phase in self.phases:
            members = tuple(agent for agent in phase.agents if agent in sequence)
            if members:
                phases.append(
                    ExecutionPhase(
                        name=phase.name,
                        goal=phase.goal,
                        agents=members,
                    )
                )
                covered.update(members)

        leftovers = [agent for agent in sequence if agent not in covered]
        if leftovers:
            phases.append(
                ExecutionPhase(
                    name="ad-hoc",
                    goal="Agents without explicit phase assignments.",
                    agents=tuple(leftovers),
                )
            )

        return ExecutionPlan(tuple(phases))

    def iter_agents(self) -> Sequence[str]:
        """Return the flattened execution order for the plan."""

        ordered: List[str] = []
        for phase in self.phases:
            ordered.extend(phase.agents)
        return tuple(ordered)

    def dependencies_for(self, agent_type: str) -> Tuple[str, ...]:
        """Return the agents that are planned to run before ``agent_type``."""

        key = agent_type.lower()
        predecessors: List[str] = []
        for phase in self.phases:
            if key in phase.agents:
                for agent in phase.agents:
                    if agent == key:
                        break
                    predecessors.append(agent)
                break
            predecessors.extend(phase.agents)
        return tuple(predecessors)

    def to_dict(self) -> dict[str, object]:
        return {"phases": [phase.to_dict() for phase in self.phases]}


def build_default_plan() -> ExecutionPlan:
    """Return the default execution plan covering all built-in agents."""

    phases = (
        ExecutionPhase(
            name="foundation",
            goal="Prepare infrastructure, security and remote access baselines.",
            agents=("nova",),
        ),
        ExecutionPhase(
            name="model-operations",
            goal="Provision model tooling and automation pipelines.",
            agents=("orion", "chronos"),
        ),
        ExecutionPhase(
            name="data-services",
            goal="Bring database and vector knowledge stores online.",
            agents=("lumina",),
        ),
        ExecutionPhase(
            name="experience",
            goal="Deliver avatar and interaction capabilities for Sophia.",
            agents=("echo",),
        ),
        ExecutionPhase(
            name="observability",
            goal="Activate dashboards, sentiment analytics and efficiency tracking.",
            agents=("aura",),
        ),
    )
    return ExecutionPlan(phases)


__all__ = [
    "ExecutionPhase",
    "ExecutionPlan",
    "build_default_plan",
]

