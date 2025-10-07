"""Agent registry used by the orchestrator."""

from __future__ import annotations

from typing import Dict, Type

from .base import BaseAgent
from .aura import AuraAgent
from .chronos import ChronosAgent
from .echo import EchoAgent
from .lumina import LuminaAgent
from .nova import NovaAgent
from .orion import OrionAgent


_REGISTRY: Dict[str, Type[BaseAgent]] = {
    agent.agent_type: agent
    for agent in (AuraAgent, ChronosAgent, EchoAgent, LuminaAgent, NovaAgent, OrionAgent)
}


def get_agent_class(agent_type: str) -> Type[BaseAgent] | None:
    """Return the registered agent class for ``agent_type`` if available."""

    return _REGISTRY.get(agent_type.lower())


def list_agent_types() -> list[str]:
    """Return sorted list of registered agent identifiers."""

    return sorted(_REGISTRY.keys())


__all__ = ["get_agent_class", "list_agent_types"]
