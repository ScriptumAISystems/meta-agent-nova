"""DGX hardware and environment audit utilities."""

from __future__ import annotations

import json
import shutil
import socket
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Sequence

from .setup import _resolve_root
from .checks import check_gpu


@dataclass(slots=True)
class AuditCheck:
    """Represents the outcome of a single audit check."""

    name: str
    status: str
    details: List[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {"name": self.name, "status": self.status, "details": list(self.details)}


@dataclass(slots=True)
class DGXAuditResult:
    """Aggregated view of the DGX audit run."""

    timestamp: datetime
    checks: List[AuditCheck]
    report_path: Path
    log_path: Path

    @property
    def passed(self) -> bool:
        return all(check.status == "ok" for check in self.checks)

    def to_dict(self) -> dict[str, object]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "passed": self.passed,
            "checks": [check.to_dict() for check in self.checks],
            "report_path": str(self.report_path),
            "log_path": str(self.log_path),
        }

    def to_markdown(self) -> str:
        lines: List[str] = [
            "# DGX Audit Report",
            "",
            f"* Generated: {self.timestamp.isoformat()}",
            f"* Overall status: {'pass' if self.passed else 'attention required'}",
            "",
        ]
        for check in self.checks:
            icon = "✅" if check.status == "ok" else "⚠️" if check.status == "warning" else "❌"
            lines.append(f"## {check.name}")
            lines.append(f"- Status: {icon} {check.status}")
            if check.details:
                lines.append("- Details:")
                for detail in check.details:
                    lines.append(f"  - {detail}")
            lines.append("")
        return "\n".join(lines).strip() + "\n"


def _normalise_status(flag: bool | None, *, success: str, failure: str) -> tuple[str, List[str]]:
    if flag is True:
        return "ok", [success]
    if flag is False:
        return "warning", [failure]
    return "warning", ["Check could not be executed."]


def _run_cuda_probe() -> tuple[str, List[str]]:
    executable = shutil.which("nvidia-smi")
    if not executable:
        return "warning", ["nvidia-smi not available in PATH"]
    try:
        output = subprocess.check_output(
            [executable, "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader"],
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return "warning", [f"Failed to execute nvidia-smi: {exc}"]
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    if not lines:
        return "warning", ["nvidia-smi returned no GPU entries"]
    return "ok", [line.replace(",", " | ") for line in lines]


def _check_ports(ports: Sequence[int], *, host: str = "127.0.0.1", timeout: float = 0.2) -> tuple[str, List[str]]:
    details: List[str] = []
    all_ok = True
    for port in ports:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
        if result == 0:
            details.append(f"Port {port} reachable on {host}")
        else:
            all_ok = False
            details.append(f"Port {port} closed or filtered (code={result})")
    return ("ok" if all_ok else "warning", details)


def _check_filesystem(root: Path) -> tuple[str, List[str]]:
    details: List[str] = []
    try:
        logs_dir = root / "logs"
        reports_dir = root / "reports"
        logs_dir.mkdir(parents=True, exist_ok=True)
        reports_dir.mkdir(parents=True, exist_ok=True)
        probe_file = logs_dir / "dgx_write_test.log"
        probe_file.write_text("dgx-audit-write-test\n", encoding="utf-8")
        details.append(f"Write access confirmed in {logs_dir}")
        details.append(f"Reports directory available at {reports_dir}")
        return "ok", details
    except OSError as exc:
        return "error", [f"Filesystem write failed: {exc}"]


def run_dgx_audit(
    *,
    base_path: Path | None = None,
    ports: Iterable[int] = (22, 443, 50051),
) -> DGXAuditResult:
    """Execute the DGX audit and persist a Markdown report."""

    root = _resolve_root(base_path)
    timestamp = datetime.utcnow()

    gpu_info = check_gpu()
    gpu_status, gpu_details = _normalise_status(
        gpu_info.get("available"),
        success="GPU detected via system check.",
        failure=gpu_info.get("details", "GPU unavailable"),
    )
    cuda_status, cuda_details = _run_cuda_probe()
    network_status, network_details = _check_ports(list(ports))
    fs_status, fs_details = _check_filesystem(root)

    checks = [
        AuditCheck(name="GPU Availability", status=gpu_status, details=gpu_details),
        AuditCheck(name="CUDA Probe", status=cuda_status, details=cuda_details),
        AuditCheck(name="Network Ports", status=network_status, details=network_details),
        AuditCheck(name="Filesystem Access", status=fs_status, details=fs_details),
    ]

    report_dir = root / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "dgx_audit_report.md"

    log_dir = root / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "dgx_audit.jsonl"
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"timestamp": timestamp.isoformat(), "checks": [c.to_dict() for c in checks]}) + "\n")

    result = DGXAuditResult(timestamp=timestamp, checks=checks, report_path=report_path, log_path=log_path)
    report_path.write_text(result.to_markdown(), encoding="utf-8")
    return result


__all__ = ["AuditCheck", "DGXAuditResult", "run_dgx_audit"]
