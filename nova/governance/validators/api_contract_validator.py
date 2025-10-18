"""Validation for cross-system governance API contracts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse
import json
import urllib.request

from . import ValidatorResult


@dataclass(slots=True)
class APIContractValidator:
    """Ensures Nova, Spark Sophia and Aurora share a consistent contract."""

    memory_schema_resource: str
    ethics_resource: str
    name: str = "governance-api-contract"

    def _load_json(self, resource: str) -> dict[str, object]:
        parsed = urlparse(resource)
        if parsed.scheme in {"http", "https"}:
            with urllib.request.urlopen(resource, timeout=5) as response:  # pragma: no cover - network
                payload = response.read().decode("utf-8")
        else:
            payload = Path(resource).read_text(encoding="utf-8")
        data = json.loads(payload)
        if not isinstance(data, dict):
            raise TypeError("API resources must be JSON objects")
        return data

    def validate(self) -> ValidatorResult:
        try:
            schema = self._load_json(self.memory_schema_resource)
            ethics = self._load_json(self.ethics_resource)
        except Exception as exc:  # pragma: no cover - defensive
            return ValidatorResult(
                name=self.name,
                status="FAIL",
                summary="Unable to load contract resources",
                details=[f"error: {exc}"]
            )

        messages: list[str] = []
        status = "PASS"
        required_tables = {"governance_events", "risk_assessments"}
        tables = {
            table.get("name")
            for table in schema.get("tables", [])
            if isinstance(table, dict)
        }
        missing_tables = sorted(required_tables - tables)
        if missing_tables:
            status = "FAIL"
            messages.append(f"missing tables: {', '.join(missing_tables)}")
        required_contract_version = str(schema.get("contract_version", "")).strip()
        aurora_version = str(ethics.get("contract_version", "")).strip()
        if not required_contract_version or not aurora_version:
            status = "FAIL"
            messages.append("contract_version must be present in both schema and ethics")
        elif required_contract_version != aurora_version:
            status = "WARN" if status == "PASS" else status
            messages.append(
                f"contract version mismatch: schema={required_contract_version}, aurora={aurora_version}"
            )
        policy_reference = ethics.get("policy_reference")
        if not isinstance(policy_reference, dict) or "policy_version" not in policy_reference:
            status = "WARN" if status == "PASS" else status
            messages.append("policy_reference must include policy_version")

        if not messages:
            messages.append(f"contract_version={required_contract_version}")
        summary = "Governance API contract verified" if status == "PASS" else "Governance contract drift detected"
        return ValidatorResult(name=self.name, status=status, summary=summary, details=messages)


__all__ = ["APIContractValidator"]
