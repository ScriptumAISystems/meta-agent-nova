"""Agent role classes for Nova Blueprints."""

from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class AgentRole:
    """Base class for agent role blueprints."""
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PlannerBlueprint(AgentRole):
    """Planner blueprint for planning tasks and coordinating sub-agents."""
    description: str = "Plans tasks and coordinates sub-agents"


@dataclass
class CoderBlueprint(AgentRole):
    """Coder blueprint for writing code based on specifications."""
    description: str = "Writes code based on specifications"


@dataclass
class TesterBlueprint(AgentRole):
    """Tester blueprint for testing code for bugs and issues."""
    description: str = "Tests the code for bugs and issues"


@dataclass
class OpsBlueprint(AgentRole):
    """Ops blueprint for handling deployment and operations tasks."""
    description: str = "Handles deployment and operations tasks"


# Mapping of agent type names to blueprint classes
AGENT_BLUEPRINT_CLASSES = {
    "planner": PlannerBlueprint,
    "coder": CoderBlueprint,
    "tester": TesterBlueprint,
    "ops": OpsBlueprint,
}


def get_blueprint_class(agent_type: str):
    """Return the blueprint class for a given agent type name.

    Args:
        agent_type: The name of the agent type.

    Returns:
        The class corresponding to the agent type or None if not found.
    """
    return AGENT_BLUEPRINT_CLASSES.get(agent_type.lower())
