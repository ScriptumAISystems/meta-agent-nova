"""System setup utilities for Nova."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from pathlib import Path
from typing import Iterable, List, Mapping

from ..monitoring.logging import log_info, log_warning

DEFAULT_DIRECTORIES = ("logs", "configs", "artifacts")
DEFAULT_CONFIG = {
    "version": 1,
    "telemetry": {"enabled": True},
}


@dataclass(slots=True)
class EnvironmentReport:
    """Summary of the environment preparation step."""

    root: Path
    created_paths: List[Path] = field(default_factory=list)
    config_file: Path | None = None

    def to_dict(self) -> dict:
        return {
            "root": str(self.root),
            "created_paths": [str(path) for path in self.created_paths],
            "config_file": str(self.config_file) if self.config_file else None,
        }


@dataclass(slots=True)
class InstallationReport:
    """Summary of the simulated package installation step."""

    requested: List[str]
    installed: List[str]
    skipped: List[str]
    dry_run: bool = True

    def to_dict(self) -> dict:
        return {
            "requested": list(self.requested),
            "installed": list(self.installed),
            "skipped": list(self.skipped),
            "dry_run": self.dry_run,
        }


@dataclass(slots=True)
class OSConfiguration:
    """Representation of OS configuration adjustments."""

    settings: Mapping[str, str]

    def to_dict(self) -> dict:
        return {"settings": dict(self.settings)}


def _resolve_root(base_path: Path | None = None) -> Path:
    if base_path is not None:
        return base_path
    env_value = os.environ.get("NOVA_HOME")
    if env_value:
        return Path(env_value).expanduser()
    return Path.cwd() / ".nova"


def prepare_environment(base_path: Path | None = None) -> EnvironmentReport:
    """Create required directories and configuration scaffolding."""

    root = _resolve_root(base_path)
    created: List[Path] = []
    if not root.exists():
        root.mkdir(parents=True, exist_ok=True)
        created.append(root)

    for directory in DEFAULT_DIRECTORIES:
        path = root / directory
        if not path.exists():
            path.mkdir(parents=True)
            created.append(path)

    config_file = root / "configs" / "settings.json"
    if not config_file.exists():
        config_file.write_text(json.dumps(DEFAULT_CONFIG, indent=2), encoding="utf-8")
        created.append(config_file)

    log_info(f"Environment prepared at {root} (created {len(created)} resources).")
    return EnvironmentReport(root=root, created_paths=created, config_file=config_file)


def install_packages(packages: Iterable[str], dry_run: bool = True) -> InstallationReport:
    """Simulate package installation while validating input."""

    unique_packages: List[str] = []
    seen = set()
    skipped: List[str] = []
    for package in packages:
        package = package.strip()
        if not package:
            continue
        package_lower = package.lower()
        if package_lower in seen:
            skipped.append(package)
            continue
        unique_packages.append(package)
        seen.add(package_lower)

    if not unique_packages:
        log_warning("No packages requested for installation.")

    installed = unique_packages if not dry_run else []
    log_info(
        "Package installation "
        + ("simulated" if dry_run else "executed")
        + f" for: {', '.join(unique_packages) if unique_packages else 'nothing'}"
    )
    return InstallationReport(
        requested=unique_packages,
        installed=installed,
        skipped=skipped,
        dry_run=dry_run,
    )


def configure_os(settings: Mapping[str, str] | None = None) -> OSConfiguration:
    """Simulate application of operating system tweaks."""

    applied = {"timezone": "UTC", "file_descriptor_limit": "8192"}
    if settings:
        applied.update(settings)
    log_info(
        "OS configuration updated: "
        + ", ".join(f"{key}={value}" for key, value in applied.items())
    )
    return OSConfiguration(settings=applied)


__all__ = [
    "EnvironmentReport",
    "InstallationReport",
    "OSConfiguration",
    "configure_os",
    "install_packages",
    "prepare_environment",
]
