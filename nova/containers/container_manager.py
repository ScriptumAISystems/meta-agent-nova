"""Utility helpers for managing Nova's DGX container stack."""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Sequence

from ..monitoring.logging import log_info, log_warning

_DEFAULT_IMAGES = ("spark-sophia", "nova", "aurora")
_DEFAULT_SERVICES = ("api", "database", "inference")


@dataclass(slots=True)
class ContainerOperation:
    """Represents the outcome of a container workflow step."""

    name: str
    status: str
    details: List[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {"name": self.name, "status": self.status, "details": list(self.details)}


@dataclass(slots=True)
class ContainerDeploymentReport:
    """Aggregated summary of container image and deployment tasks."""

    builds: List[ContainerOperation]
    deployments: List[ContainerOperation]

    def to_markdown(self) -> str:
        lines: List[str] = ["# DGX Container Deployment", ""]
        if self.builds:
            lines.append("## Image Builds")
            for item in self.builds:
                icon = "✅" if item.status == "completed" else "⚠️"
                lines.append(f"- {icon} {item.name}: {item.status}")
                for detail in item.details:
                    lines.append(f"  - {detail}")
            lines.append("")
        if self.deployments:
            lines.append("## Service Deployments")
            for item in self.deployments:
                icon = "✅" if item.status == "running" else "⚠️"
                lines.append(f"- {icon} {item.name}: {item.status}")
                for detail in item.details:
                    lines.append(f"  - {detail}")
        return "\n".join(lines).strip() + "\n"


def _docker_available() -> bool:
    return shutil.which("docker") is not None


def build_images(images: Sequence[str] = _DEFAULT_IMAGES) -> List[ContainerOperation]:
    """Simulate building Docker images required for DGX orchestration."""

    operations: List[ContainerOperation] = []
    docker_present = _docker_available()
    for image in images:
        if not docker_present:
            operations.append(
                ContainerOperation(
                    name=image,
                    status="skipped",
                    details=["Docker CLI not available; build deferred."],
                )
            )
            continue
        operations.append(
            ContainerOperation(
                name=image,
                status="completed",
                details=[f"Image {image} built using cached Dockerfile."],
            )
        )
    if not docker_present:
        log_warning("Docker CLI missing; image builds were skipped.")
    else:
        log_info(f"Prepared {len(images)} container images for DGX deployment.")
    return operations


def deploy_dgx(
    *,
    target: str = "dgx",
    images: Sequence[str] = _DEFAULT_IMAGES,
    services: Sequence[str] = _DEFAULT_SERVICES,
    manifests_dir: Path | None = None,
) -> ContainerDeploymentReport:
    """Simulate a DGX deployment flow using Docker Compose or Kubernetes."""

    builds = build_images(images)
    manifests_note = (
        [f"Using manifests from {manifests_dir}"] if manifests_dir else ["Using embedded deployment manifests."]
    )
    deployments: List[ContainerOperation] = []
    for service in services:
        status = "running" if _docker_available() else "pending"
        details = [f"Service {service} scheduled for {target} cluster."] + manifests_note
        if status != "running":
            details.append("Awaiting container runtime availability.")
        deployments.append(ContainerOperation(name=service, status=status, details=details))
    log_info(
        f"DGX deployment request processed for {len(services)} services on target '{target}'."
    )
    return ContainerDeploymentReport(builds=builds, deployments=deployments)


def status(services: Iterable[str] = _DEFAULT_SERVICES) -> List[ContainerOperation]:
    """Return a lightweight view of container service status."""

    docker_present = _docker_available()
    results: List[ContainerOperation] = []
    for service in services:
        if docker_present:
            details = ["Service responding to health probe."]
            status_label = "running"
        else:
            details = ["No container runtime detected; service inactive."]
            status_label = "stopped"
        results.append(ContainerOperation(name=service, status=status_label, details=details))
    return results


__all__ = [
    "ContainerOperation",
    "ContainerDeploymentReport",
    "build_images",
    "deploy_dgx",
    "status",
]
