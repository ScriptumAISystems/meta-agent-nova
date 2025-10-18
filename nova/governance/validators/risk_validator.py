"""Validation of the Spark Sophia risk register."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse
import json
import urllib.request

from . import ValidatorResult


@dataclass(slots=True)
class RiskValidator:
    """Ensures the risk register is populated and properly structured."""

    resource: str
    name: str = "spark-risk-register"

    def _load_register(self) -> list[dict[str, object]]:
        parsed = urlparse(self.resource)
        if parsed.scheme in {"http", "https"}:
            with urllib.request.urlopen(self.resource, timeout=5) as response:  # pragma: no cover - network
                payload = response.read().decode("utf-8")
        else:
            payload = Path(self.resource).read_text(encoding="utf-8")
        data = json.loads(payload)
        if isinstance(data, dict):
            return list(data.get("risks", []))
        if isinstance(data, list):
            return list(data)
        raise TypeError("risk register must be list or dict with 'risks'")

    def validate(self) -> ValidatorResult:
        try:
            risks = self._load_register()
        except Exception as exc:  # pragma: no cover - defensive
            return ValidatorResult(
                name=self.name,
                status="FAIL",
                summary="Unable to load risk register",
                details=[f"error: {exc}"]
            )

        messages: list[str] = []
        status = "PASS"
        if not risks:
            status = "WARN"
            messages.append("risk register is empty")
        for index, risk in enumerate(risks, start=1):
            issues = _validate_risk_entry(risk)
            if issues:
                status = "FAIL"
                messages.append(f"risk #{index}: {', '.join(issues)}")
        if not messages:
            messages.append(f"risks={len(risks)} entries validated")
        summary = "Risk register validated" if status == "PASS" else "Risk register issues detected"
        return ValidatorResult(name=self.name, status=status, summary=summary, details=messages)


def _validate_risk_entry(risk: dict[str, object]) -> list[str]:
    issues: list[str] = []
    required = {"id", "category", "severity", "status"}
    missing = sorted(required - risk.keys())
    if missing:
        issues.append(f"missing fields: {', '.join(missing)}")
    severity = str(risk.get("severity", "")).upper()
    if severity not in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}:
        issues.append("severity must be one of LOW, MEDIUM, HIGH, CRITICAL")
    status = str(risk.get("status", "")).upper()
    if status not in {"OPEN", "MITIGATED", "ACCEPTED", "CLOSED"}:
        issues.append("status must be OPEN, MITIGATED, ACCEPTED, CLOSED")
    if "controls" not in risk or not isinstance(risk.get("controls"), list):
        issues.append("controls must be a list of mitigations")
    return issues


__all__ = ["RiskValidator"]
