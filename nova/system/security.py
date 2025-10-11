"""Security audit utilities for Nova."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Iterable, List, Tuple

_TRUE_VALUES = {"1", "true", "yes", "enabled", "on"}
_FALSE_VALUES = {"0", "false", "no", "disabled", "off"}


@dataclass(slots=True)
class SecurityControlStatus:
    """Represents the status of an individual security control."""

    name: str
    status: str
    details: str

    def to_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "status": self.status,
            "details": self.details,
        }


@dataclass(slots=True)
class SecurityAuditReport:
    """Structured summary of a security audit run."""

    controls: Tuple[SecurityControlStatus, ...]
    findings: Tuple[str, ...]

    @property
    def passed(self) -> bool:
        return all(control.status == "ok" for control in self.controls) and not self.findings

    def to_dict(self) -> dict[str, object]:
        return {
            "passed": self.passed,
            "controls": [control.to_dict() for control in self.controls],
            "findings": list(self.findings),
        }

    def to_markdown(self) -> str:
        lines: List[str] = [
            "# Security Audit Report",
            "",
            f"* Overall status: {'pass' if self.passed else 'attention required'}",
            "",
            "## Controls",
        ]
        for control in self.controls:
            lines.append(f"- **{control.name}**: {control.status} — {control.details}")
        lines.append("")
        lines.append("## Findings")
        if not self.findings:
            lines.append("- No outstanding findings.")
        else:
            lines.extend(f"- {finding}" for finding in self.findings)
        return "\n".join(lines).strip()


def export_security_audit_report(
    report: "SecurityAuditReport", destination: Path
) -> Path:
    """Persist a security audit report as Markdown and return the output path."""

    output_path = destination.expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report.to_markdown() + "\n", encoding="utf-8")
    return output_path


def _resolve_flag(value: bool | None, env_var: str) -> bool | None:
    if value is not None:
        return bool(value)
    env_value = os.environ.get(env_var)
    if env_value is None:
        return None
    text = env_value.strip().lower()
    if text in _TRUE_VALUES:
        return True
    if text in _FALSE_VALUES:
        return False
    return None


def _control_from_flag(
    name: str,
    flag: bool | None,
    *,
    success_detail: str,
    failure_detail: str,
    unknown_detail: str,
) -> SecurityControlStatus:
    if flag is True:
        status = "ok"
        details = success_detail
    elif flag is False:
        status = "attention"
        details = failure_detail
    else:
        status = "unknown"
        details = unknown_detail
    return SecurityControlStatus(name=name, status=status, details=details)


def run_security_audit(
    *,
    firewall_enabled: bool | None = None,
    antivirus_enabled: bool | None = None,
    policies_enforced: bool | None = None,
    extra_findings: Iterable[str] | None = None,
) -> SecurityAuditReport:
    """Simulate a security audit across Nova's key governance controls."""

    firewall_flag = _resolve_flag(firewall_enabled, "NOVA_FIREWALL_ENABLED")
    antivirus_flag = _resolve_flag(antivirus_enabled, "NOVA_ANTIVIRUS_ENABLED")
    policies_flag = _resolve_flag(policies_enforced, "NOVA_OPA_POLICIES_ENFORCED")

    controls = (
        _control_from_flag(
            "Firewall",
            firewall_flag,
            success_detail="Firewall service enabled with logging.",
            failure_detail="Firewall disabled or unreachable.",
            unknown_detail="Firewall status unknown; manual verification required.",
        ),
        _control_from_flag(
            "Anti-Virus",
            antivirus_flag,
            success_detail="Anti-virus definitions up to date.",
            failure_detail="Anti-virus protection disabled.",
            unknown_detail="Anti-virus status unknown; run diagnostics.",
        ),
        _control_from_flag(
            "OPA Policies",
            policies_flag,
            success_detail="OPA policies enforced with daily rotation.",
            failure_detail="OPA policies not enforced.",
            unknown_detail="OPA policy enforcement unknown; review configuration.",
        ),
    )

    findings: List[str] = []
    for control in controls:
        if control.status != "ok":
            findings.append(f"{control.name}: {control.details}")
    if extra_findings:
        findings.extend(extra_findings)

    return SecurityAuditReport(controls=controls, findings=tuple(findings))


__all__ = [
    "SecurityControlStatus",
    "SecurityAuditReport",
    "export_security_audit_report",
    "run_security_audit",
]
