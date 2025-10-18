"""Validator interfaces for the governance integrity suite."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence


class Validator(Protocol):
    """Protocol implemented by integrity validators."""

    name: str

    def validate(self) -> "ValidatorResult":
        """Execute the validator and return a structured result."""


@dataclass(slots=True)
class ValidatorResult:
    """Standardised outcome returned by validators."""

    name: str
    status: str
    summary: str
    details: Sequence[str]

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "status": self.status,
            "summary": self.summary,
            "details": list(self.details),
        }


__all__ = ["Validator", "ValidatorResult"]
