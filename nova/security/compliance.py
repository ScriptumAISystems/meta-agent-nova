"""Compliance helper utilities for ISO 27001 alignment."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable

ISO_27001_CONTROLS: Dict[str, str] = {
    "A.6.1.2": "Information security coordination",
    "A.8.2.2": "Information classification",
    "A.12.4.1": "Event logging",
    "A.12.4.3": "Administrator and operator logs",
    "A.12.6.2": "Restrictions on software installation",
    "A.16.1.7": "Collection of evidence",
}


@dataclass(frozen=True)
class ControlEvidence:
    """Represents documentary evidence for an implemented control."""

    control_id: str
    description: str
    evidence_location: str


class ComplianceRegistry:
    """Tracks how platform controls satisfy ISO 27001 requirements."""

    def __init__(self) -> None:
        self._entries: Dict[str, ControlEvidence] = {}

    def register(self, evidence: ControlEvidence) -> None:
        if evidence.control_id not in ISO_27001_CONTROLS:
            raise KeyError(f"Unknown ISO 27001 control {evidence.control_id}")
        self._entries[evidence.control_id] = evidence

    def evidence(self) -> Iterable[ControlEvidence]:
        return self._entries.values()


__all__ = ["ISO_27001_CONTROLS", "ControlEvidence", "ComplianceRegistry"]
