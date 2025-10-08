"""Container runtime validation utilities for Nova."""

from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
import shutil
import subprocess
from typing import Iterable, List, Sequence

from ..monitoring.logging import log_info, log_warning


@dataclass(slots=True)
class RuntimeCheckResult:
    """Outcome of a container runtime verification."""

    name: str
    binary: str
    found: bool
    version: str | None
    health: str
    notes: List[str] = field(default_factory=list)
    config_ok: bool | None = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "binary": self.binary,
            "found": self.found,
            "version": self.version,
            "health": self.health,
            "notes": list(self.notes),
            "config_ok": self.config_ok,
        }


@dataclass(slots=True)
class ContainerInspectionReport:
    """Aggregated view of container runtime checks."""

    runtimes: List[RuntimeCheckResult]

    def all_healthy(self) -> bool:
        return all(result.health == "ok" for result in self.runtimes)

    def to_dict(self) -> dict:
        return {
            "runtimes": [result.to_dict() for result in self.runtimes],
            "all_healthy": self.all_healthy(),
        }

    def to_markdown(self) -> str:
        lines: list[str] = ["# Nova Container Runtime Check", ""]
        for result in self.runtimes:
            icon = "✅" if result.health == "ok" else "⚠️" if result.health == "warning" else "❌"
            lines.append(f"## {result.name}")
            lines.append(f"- Status: {icon} {result.health}")
            lines.append(f"- Binary: {result.binary}")
            lines.append(f"- Gefunden: {'Ja' if result.found else 'Nein'}")
            if result.version:
                lines.append(f"- Version: {result.version}")
            if result.config_ok is not None:
                lines.append(
                    "- Kubeconfig: "
                    + ("✅ vorhanden" if result.config_ok else "⚠️ nicht gefunden")
                )
            if result.notes:
                lines.append("")
                lines.append("### Hinweise")
                for note in result.notes:
                    lines.append(f"- {note}")
            lines.append("")
        return "\n".join(lines).strip()


def _run_version_command(binary: str, version_args: Sequence[str]) -> tuple[str | None, list[str], str]:
    """Execute the version command and capture output and health state."""

    notes: list[str] = []
    try:
        completed = subprocess.run(  # noqa: S603,S607 - command built from trusted inputs
            [binary, *version_args],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except FileNotFoundError:
        notes.append("Binary war beim Versionsaufruf nicht verfügbar.")
        return None, notes, "warning"
    except subprocess.TimeoutExpired:
        notes.append("Versionsabfrage hat das Zeitlimit überschritten.")
        return None, notes, "warning"
    except Exception as exc:  # pragma: no cover - defensive fallback
        notes.append(f"Fehler beim Abrufen der Version: {exc}")
        return None, notes, "warning"

    output = (completed.stdout or "").strip() or (completed.stderr or "").strip()
    version = output.splitlines()[0] if output else None
    if completed.returncode != 0:
        notes.append(f"Versionskommando endete mit Code {completed.returncode}.")
        if output:
            notes.append(output)
        return version, notes, "warning"
    return version, notes, "ok"


def check_container_runtime(
    name: str,
    binary: str,
    *,
    version_args: Sequence[str] = ("--version",),
    config_paths: Iterable[Path] | None = None,
) -> RuntimeCheckResult:
    """Verify the availability of a container runtime binary and configuration."""

    binary_path = shutil.which(binary)
    if binary_path is None:
        notes = [f"Binary '{binary}' wurde nicht im PATH gefunden."]
        return RuntimeCheckResult(
            name=name,
            binary=binary,
            found=False,
            version=None,
            health="missing",
            notes=notes,
            config_ok=None,
        )

    version, notes, health = _run_version_command(binary, version_args)

    config_ok: bool | None = None
    if config_paths:
        expanded_paths = []
        for path in config_paths:
            expanded_paths.append(path.expanduser())
        unique_paths = []
        seen = set()
        for path in expanded_paths:
            key = path.resolve()
            if key in seen:
                continue
            seen.add(key)
            unique_paths.append(path)
        existing = [path for path in unique_paths if path.exists()]
        if existing:
            config_ok = True
            note = "Gefundene Kubeconfig-Dateien: " + ", ".join(str(path) for path in existing)
            notes.append(note)
        else:
            config_ok = False
            notes.append("Keine Kubeconfig-Dateien gefunden.")
            if health == "ok":
                health = "warning"

    return RuntimeCheckResult(
        name=name,
        binary=binary,
        found=True,
        version=version,
        health=health,
        notes=notes,
        config_ok=config_ok,
    )


def _collect_kubeconfig_candidates(explicit: Path | None) -> list[Path]:
    candidates: list[Path] = []
    if explicit:
        candidates.append(explicit)
    env_value = os.environ.get("KUBECONFIG")
    if env_value:
        for raw_path in env_value.split(os.pathsep):
            raw_path = raw_path.strip()
            if raw_path:
                candidates.append(Path(raw_path))
    default_path = Path.home() / ".kube" / "config"
    candidates.append(default_path)
    return candidates


def inspect_container_runtimes(kubeconfig: Path | None = None) -> ContainerInspectionReport:
    """Inspect Docker and Kubernetes runtime availability."""

    kubeconfig_candidates = _collect_kubeconfig_candidates(kubeconfig)

    results = [
        check_container_runtime("Docker Engine", "docker"),
        check_container_runtime(
            "Kubernetes CLI",
            "kubectl",
            version_args=("version", "--client", "--short"),
            config_paths=kubeconfig_candidates,
        ),
    ]

    return ContainerInspectionReport(runtimes=results)


def log_container_report(report: ContainerInspectionReport) -> None:
    """Emit the inspection report via the Nova logger."""

    for line in report.to_markdown().splitlines():
        log_info(line)
    if not report.all_healthy():
        log_warning(
            "Container-Prüfung meldet Warnungen oder fehlende Runtimes. Bitte Installationsplan prüfen."
        )
    else:
        log_info("Alle Container-Runtimes sind einsatzbereit.")


__all__ = [
    "ContainerInspectionReport",
    "RuntimeCheckResult",
    "check_container_runtime",
    "inspect_container_runtimes",
    "log_container_report",
]
