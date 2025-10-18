"""Governance integrity orchestration for Nova."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Sequence

from .validators import ValidatorResult
from .validators.api_contract_validator import APIContractValidator
from .validators.policy_validator import PolicyValidator
from .validators.risk_validator import RiskValidator


@dataclass(slots=True)
class IntegrityCheckConfig:
    """Configuration for running governance integrity checks."""

    policy_resource: str
    risk_resource: str
    memory_schema_resource: str
    ethics_resource: str

    @classmethod
    def from_file(cls, path: str | os.PathLike[str]) -> "IntegrityCheckConfig":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(
            policy_resource=str(payload["policy_resource"]),
            risk_resource=str(payload["risk_resource"]),
            memory_schema_resource=str(payload["memory_schema_resource"]),
            ethics_resource=str(payload["ethics_resource"]),
        )


@dataclass(slots=True)
class IntegrityReport:
    """Aggregated report returned by the integrity suite."""

    generated_at: datetime
    results: Sequence[ValidatorResult]

    @property
    def overall_status(self) -> str:
        statuses = {result.status.upper() for result in self.results}
        if "FAIL" in statuses:
            return "FAIL"
        if "WARN" in statuses:
            return "WARN"
        return "PASS"

    def as_dict(self) -> dict[str, object]:
        return {
            "generated_at": self.generated_at.isoformat(),
            "overall_status": self.overall_status,
            "results": [result.as_dict() for result in self.results],
        }


def run_integrity_checks(config: IntegrityCheckConfig) -> IntegrityReport:
    validators = [
        PolicyValidator(resource=config.policy_resource),
        RiskValidator(resource=config.risk_resource),
        APIContractValidator(
            memory_schema_resource=config.memory_schema_resource,
            ethics_resource=config.ethics_resource,
        ),
    ]
    results: List[ValidatorResult] = []
    for validator in validators:
        results.append(validator.validate())
    return IntegrityReport(generated_at=datetime.now(timezone.utc), results=results)


def render_markdown(report: IntegrityReport) -> str:
    lines = [
        "# Governance Integrity Report",
        "",
        f"- Generated At: {report.generated_at.isoformat()}",
        f"- Overall Status: **{report.overall_status}**",
        "",
        "## Validator Breakdown",
    ]
    for result in report.results:
        lines.append(f"### {result.name}")
        lines.append(f"- Status: **{result.status}**")
        lines.append(f"- Summary: {result.summary}")
        if result.details:
            lines.append("- Details:")
            for detail in result.details:
                lines.append(f"  - {detail}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def write_reports(report: IntegrityReport, directory: str | os.PathLike[str]) -> tuple[Path, Path]:
    reports_dir = Path(directory)
    reports_dir.mkdir(parents=True, exist_ok=True)
    json_path = reports_dir / "governance_integrity.json"
    md_path = reports_dir / "governance_integrity.md"
    json_path.write_text(json.dumps(report.as_dict(), indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return json_path, md_path


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Nova governance integrity checks")
    parser.add_argument(
        "--config",
        default=Path("config/governance/integrity_config.json"),
        type=Path,
        help="Path to the integrity configuration file",
    )
    parser.add_argument(
        "--reports-dir",
        default=Path("reports"),
        type=Path,
        help="Directory where reports will be written",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    config = IntegrityCheckConfig.from_file(args.config)
    report = run_integrity_checks(config)
    write_reports(report, args.reports_dir)
    return 0 if report.overall_status != "FAIL" else 1


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
