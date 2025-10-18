"""Validation for Spark Sophia policy metadata."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
import json
import urllib.request

from . import ValidatorResult


@dataclass(slots=True)
class PolicyValidator:
    """Ensures that Spark Sophia exposes the expected policy metadata."""

    resource: str
    name: str = "spark-policy"

    def _load_policy(self) -> dict[str, object]:
        parsed = urlparse(self.resource)
        if parsed.scheme in {"http", "https"}:
            with urllib.request.urlopen(self.resource, timeout=5) as response:  # pragma: no cover - network
                payload = response.read().decode("utf-8")
        else:
            payload = Path(self.resource).read_text(encoding="utf-8")
        return json.loads(payload)

    def validate(self) -> ValidatorResult:
        messages: list[str] = []
        status = "PASS"
        try:
            payload = self._load_policy()
        except Exception as exc:  # pragma: no cover - defensive
            return ValidatorResult(
                name=self.name,
                status="FAIL",
                summary="Unable to load policy metadata",
                details=[f"error: {exc}"]
            )

        required_keys = {"policy_version", "checksum"}
        missing = sorted(required_keys - payload.keys())
        if missing:
            status = "FAIL"
            messages.append(f"missing keys: {', '.join(missing)}")
        version = str(payload.get("policy_version", "")).strip()
        if not version:
            status = "FAIL"
            messages.append("policy_version is empty")
        checksum = str(payload.get("checksum", "")).strip()
        if not checksum.startswith("sha256:"):
            status = "WARN" if status == "PASS" else status
            messages.append("checksum should be sha256 prefixed")
        updated_at = payload.get("updated_at")
        if updated_at:
            if not _is_iso_timestamp(str(updated_at)):
                status = "WARN" if status == "PASS" else status
                messages.append("updated_at is not ISO-8601 timestamp")
        else:
            messages.append("updated_at not provided")
            if status == "PASS":
                status = "WARN"

        summary = "Policy metadata loaded" if status == "PASS" else "Policy metadata requires attention"
        if not messages:
            messages.append(f"version={version}")
            messages.append(f"checksum={checksum}")
        return ValidatorResult(name=self.name, status=status, summary=summary, details=messages)


def _is_iso_timestamp(value: str) -> bool:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


__all__ = ["PolicyValidator"]
