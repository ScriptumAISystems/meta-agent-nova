"""Extended security audit helpers for DGX operations."""

from __future__ import annotations

import getpass
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from ..monitoring.logging import log_info, log_warning


@dataclass(slots=True)
class SecurityCheck:
    """Single security control evaluation."""

    name: str
    status: str
    details: List[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {"name": self.name, "status": self.status, "details": list(self.details)}


@dataclass(slots=True)
class SecurityAuditSummary:
    """Structured outcome of the security audit."""

    timestamp: datetime
    checks: List[SecurityCheck]
    report_path: Path

    @property
    def passed(self) -> bool:
        return all(check.status == "ok" for check in self.checks)

    def to_markdown(self) -> str:
        lines: List[str] = [
            "# DGX Security Audit",
            "",
            f"* Executed: {self.timestamp.isoformat()}",
            f"* Overall status: {'pass' if self.passed else 'attention required'}",
            "",
        ]
        for check in self.checks:
            icon = "✅" if check.status == "ok" else "⚠️"
            lines.append(f"## {check.name}")
            lines.append(f"- Status: {icon} {check.status}")
            for detail in check.details:
                lines.append(f"  - {detail}")
            lines.append("")
        return "\n".join(lines).strip() + "\n"

    def to_dict(self) -> Dict[str, object]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "passed": self.passed,
            "checks": [check.to_dict() for check in self.checks],
            "report_path": str(self.report_path),
        }


def _check_user_privileges() -> SecurityCheck:
    try:
        user = getpass.getuser()
    except Exception as exc:  # pragma: no cover - defensive fallback
        return SecurityCheck("User Privileges", "warning", [f"Failed to resolve user: {exc}"])
    privileged = os.geteuid() == 0 if hasattr(os, "geteuid") else False
    if privileged:
        status = "warning"
        details = [
            f"Audit executed with elevated privileges for user {user}.",
            "Consider using a non-root account for routine operations.",
        ]
    else:
        status = "ok"
        details = [f"Audit executed as user {user} without elevated rights."]
    return SecurityCheck("User Privileges", status, details)


def _check_ssh_keys() -> SecurityCheck:
    ssh_dir = Path.home() / ".ssh"
    if not ssh_dir.exists():
        return SecurityCheck("SSH Keys", "warning", ["~/.ssh directory not found."])
    keys = list(ssh_dir.glob("*.pub"))
    if not keys:
        return SecurityCheck("SSH Keys", "warning", ["No public SSH keys detected under ~/.ssh."])
    details = [f"Detected {len(keys)} public SSH key(s)."]
    return SecurityCheck("SSH Keys", "ok", details)


def _check_opa_policies(base_path: Path) -> SecurityCheck:
    policy_dir = base_path / "policy" / "opa"
    if not policy_dir.exists():
        return SecurityCheck("OPA Policies", "warning", [f"Policy directory missing: {policy_dir}"])
    policies = list(policy_dir.glob("**/*.rego"))
    if not policies:
        return SecurityCheck("OPA Policies", "warning", ["No OPA policy files (*.rego) were found."])
    return SecurityCheck(
        "OPA Policies",
        "ok",
        [f"Discovered {len(policies)} policy file(s) for enforcement."],
    )


def _check_worm_logs(base_path: Path) -> SecurityCheck:
    worm_dir = base_path / "logs" / "worm"
    if not worm_dir.exists():
        return SecurityCheck("WORM Logs", "warning", ["Immutable log directory not initialised."])
    archives = list(worm_dir.glob("*.log"))
    if not archives:
        return SecurityCheck("WORM Logs", "warning", ["No immutable log archives present."])
    return SecurityCheck("WORM Logs", "ok", [f"Found {len(archives)} log snapshot(s)."])


def perform_security_audit(base_path: Path) -> SecurityAuditSummary:
    """Execute extended security checks and store a Markdown report."""

    timestamp = datetime.utcnow()
    checks = [
        _check_user_privileges(),
        _check_ssh_keys(),
        _check_opa_policies(base_path),
        _check_worm_logs(base_path),
    ]
    reports_dir = base_path / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / "security_audit_report.md"
    summary = SecurityAuditSummary(timestamp=timestamp, checks=checks, report_path=report_path)
    report_path.write_text(summary.to_markdown(), encoding="utf-8")
    log_info(f"Security audit summary stored at {report_path}")

    log_path = base_path / "logs" / "security_audit.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(summary.to_dict()) + "\n")
    if not summary.passed:
        log_warning("Security audit completed with findings requiring attention.")
    return summary


__all__ = ["SecurityCheck", "SecurityAuditSummary", "perform_security_audit"]
