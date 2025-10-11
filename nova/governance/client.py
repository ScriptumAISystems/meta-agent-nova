"""Governance API client for Nova."""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, Mapping

LOGGER = logging.getLogger("nova.governance")


@dataclass(slots=True)
class GovernanceDecision:
    """Structured response returned by the governance engine."""

    verdict: str
    rationale: str
    details: Dict[str, Any]

    @property
    def is_blocking(self) -> bool:
        return self.verdict.upper() == "BLOCK"

    @property
    def is_warning(self) -> bool:
        return self.verdict.upper() == "WARN"


class GovernanceClient:
    """Simple HTTP client that integrates with Sophia's governance endpoint."""

    def __init__(self, base_url: str, *, timeout: float = 5.0) -> None:
        if not base_url.endswith("/"):
            base_url += "/"
        self.base_url = base_url
        self.timeout = timeout

    def evaluate_action(self, action: str, payload: Mapping[str, Any]) -> GovernanceDecision:
        request = urllib.request.Request(
            f"{self.base_url}governance/evaluate",
            data=json.dumps({"action": action, "payload": dict(payload)}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = response.read().decode("utf-8")
        except urllib.error.URLError as exc:  # pragma: no cover - network fallback
            LOGGER.warning("Governance evaluation failed: %s", exc)
            return GovernanceDecision(verdict="WARN", rationale="network-error", details={})
        try:
            data = json.loads(body)
        except json.JSONDecodeError:  # pragma: no cover - defensive
            LOGGER.warning("Invalid governance response: %s", body)
            return GovernanceDecision(verdict="WARN", rationale="invalid-response", details={})
        verdict = str(data.get("verdict", "WARN")).upper()
        rationale = str(data.get("rationale", ""))
        details = data.get("details")
        if not isinstance(details, dict):
            details = {}
        return GovernanceDecision(verdict=verdict, rationale=rationale, details=details)


__all__ = ["GovernanceClient", "GovernanceDecision"]
