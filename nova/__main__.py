"""Command line entry point for Meta-Agent Nova.

Provides a simple CLI with subcommands for system setup, blueprint generation
and monitoring utilities. The implementation is intentionally light-weight and
acts as a façade over the modules in :mod:`nova.system`, :mod:`nova.blueprints`
and :mod:`nova.monitoring`.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Iterable

from .agents.registry import list_agent_types
from .system.checks import check_cpu, check_gpu, check_network
from .system.setup import configure_os, install_packages, prepare_environment
from .system.security import run_security_audit
from .system.orchestrator import Orchestrator
from .blueprints.generator import create_blueprint, list_available_blueprints
from .monitoring.alerts import notify_info, notify_warning
from .monitoring.logging import configure_logger, log_error, log_info, log_warning
from .monitoring.reports import build_markdown_test_report
from .system.tasks import (
    build_markdown_task_overview,
    filter_tasks as filter_agent_tasks,
    load_agent_tasks,
    normalise_agent_identifier,
    resolve_task_csv_path,
)


def _parse_toggle(value: str | None) -> bool | None:
    if value is None:
        return None
    lowered = value.lower()
    if lowered not in {"enabled", "disabled"}:
        raise ValueError(f"Unsupported toggle value: {value}")
    return lowered == "enabled"


DEFAULT_PACKAGES = [
    "docker",
    "kubernetes",
    "wireguard",
]


def run_setup(packages: Iterable[str] | None = None) -> None:
    """Perform system setup and installation tasks.

    The function orchestrates the stubbed system preparation utilities and logs
    a short status summary with the collected hardware checks.
    """

    configure_logger()
    log_info("Starting system setup")

    try:
        environment_report = prepare_environment()
        package_list = list(packages) if packages is not None else DEFAULT_PACKAGES
        installation_report = install_packages(package_list)
        os_report = configure_os()
    except Exception as exc:  # pragma: no cover - defensive logging
        log_error(f"System setup failed: {exc}")
        raise

    log_info(f"Environment report: {environment_report.to_dict()}")
    log_info(f"Installation report: {installation_report.to_dict()}")
    log_info(f"OS configuration: {os_report.to_dict()}")

    cpu_status = check_cpu()
    gpu_status = check_gpu()
    network_status = check_network()

    log_info(
        "CPU status: "
        + ", ".join(f"{key}={value}" for key, value in cpu_status.items())
    )
    log_info(
        "GPU status: "
        + ", ".join(f"{key}={value}" for key, value in gpu_status.items())
    )
    log_info(
        "Network status: "
        + ", ".join(f"{key}={value}" for key, value in network_status.items())
    )

    if not gpu_status.get("available", False):
        log_warning("GPU check indicates that no GPU is available.")
    if not network_status.get("online", False):
        log_warning("Network check indicates connectivity issues.")

    log_info("System setup routine finished.")


def run_blueprints() -> None:
    """Generate agent blueprints and log the output."""

    configure_logger()
    blueprints = list_available_blueprints()
    if not blueprints:
        log_warning("No blueprints are currently defined.")
        return

    log_info("Available blueprints: " + ", ".join(sorted(blueprints)))

    for agent_type in sorted(blueprints):
        blueprint = create_blueprint(agent_type)
        log_info(f"Generated blueprint for {agent_type}: {blueprint.to_dict()}")


def run_monitor() -> None:
    """Start monitoring services (placeholder)."""

    configure_logger()
    log_info("Monitoring services initialised.")
    notify_warning("Monitoring is running in stub mode.")
    notify_info("No active alerts.")


def run_audit(
    *, firewall: str | None = None, antivirus: str | None = None, policies: str | None = None
) -> None:
    """Execute the security audit workflow and log findings."""

    configure_logger()
    log_info("Starting security audit")
    report = run_security_audit(
        firewall_enabled=_parse_toggle(firewall),
        antivirus_enabled=_parse_toggle(antivirus),
        policies_enforced=_parse_toggle(policies),
    )
    for control in report.controls:
        log_info(f"[{control.status}] {control.name}: {control.details}")
    if report.passed:
        notify_info("Security audit passed with all controls in a healthy state.")
    else:
        for finding in report.findings:
            notify_warning(finding)
        notify_warning("Security audit detected issues that require attention.")
    log_info("Security audit summary (markdown):\n" + report.to_markdown())


def run_orchestration(agent_types: Iterable[str] | None = None) -> None:
    """Execute orchestrated agent workflows."""

    configure_logger()
    execution_mode = os.environ.get("NOVA_EXECUTION_MODE", "sequential")
    orchestrator = Orchestrator(agent_types, execution_mode=execution_mode)
    report = orchestrator.execute()
    log_info(f"Orchestration result: {report.to_dict()}")
    log_info("Orchestration summary (markdown):\n" + report.to_markdown())
    report_content = build_markdown_test_report(report)
    reports_dir = Path(os.environ.get("NOVA_HOME") or Path.cwd()) / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / "nova-test-report.md"
    report_path.write_text(report_content, encoding="utf-8")
    log_info(f"Stored orchestration test report at {report_path}")


def run_tasks(
    agent_filters: Iterable[str] | None = None,
    status: str | None = None,
    csv_path: Path | None = None,
) -> None:
    """Load the task overview and log a grouped summary."""

    configure_logger()
    resolved_path = resolve_task_csv_path(csv_path)
    log_info(f"Loading agent tasks from {resolved_path}")

    try:
        tasks = load_agent_tasks(resolved_path)
    except FileNotFoundError as exc:
        log_error(f"Task overview file not found: {exc}")
        raise

    filters = (
        [normalise_agent_identifier(identifier) for identifier in agent_filters]
        if agent_filters
        else None
    )
    filtered_tasks = filter_agent_tasks(tasks, filters, status)
    if not filtered_tasks:
        log_warning("No tasks matched the provided filters.")
        return

    overview = build_markdown_task_overview(filtered_tasks)
    for line in overview.splitlines():
        log_info(line)


def build_parser() -> argparse.ArgumentParser:
    """Construct the argument parser for the CLI."""

    parser = argparse.ArgumentParser(
        prog="nova",
        description="Meta-Agent Nova command line interface",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    setup_parser = subparsers.add_parser(
        "setup", help="Perform system setup and installation tasks"
    )
    setup_parser.add_argument(
        "--packages",
        nargs="*",
        metavar="PACKAGE",
        help="Optional list of packages to install (defaults to core tools).",
    )

    subparsers.add_parser(
        "blueprints", help="Generate agent blueprints"
    )
    subparsers.add_parser(
        "monitor", help="Start monitoring services"
    )

    audit_parser = subparsers.add_parser(
        "audit", help="Run the Nova security audit"
    )
    audit_parser.add_argument(
        "--firewall", choices=("enabled", "disabled"), help="Override firewall status for the audit."
    )
    audit_parser.add_argument(
        "--antivirus", choices=("enabled", "disabled"), help="Override anti-virus status for the audit."
    )
    audit_parser.add_argument(
        "--policies", choices=("enabled", "disabled"), help="Override OPA policy status for the audit."
    )

    orchestrate_parser = subparsers.add_parser(
        "orchestrate", help="Run the registered agents sequentially"
    )
    orchestrate_parser.add_argument(
        "--agents",
        nargs="*",
        metavar="AGENT",
        choices=list_agent_types(),
        help="Subset of agents to orchestrate (defaults to all registered agents).",
    )

    tasks_parser = subparsers.add_parser(
        "tasks", help="Display the agent task overview"
    )
    tasks_parser.add_argument(
        "--agent",
        nargs="*",
        metavar="AGENT",
        help="Filter tasks by agent identifier (e.g. nova, orion).",
    )
    tasks_parser.add_argument(
        "--status",
        metavar="STATUS",
        help="Filter tasks by a specific status label (case-insensitive).",
    )
    tasks_parser.add_argument(
        "--csv",
        type=Path,
        metavar="PATH",
        help="Optional path to an alternative task overview CSV file.",
    )

    return parser


def main(argv: list[str] | None = None) -> None:
    """Entrypoint used by ``python -m nova``."""

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "setup":
        run_setup(args.packages)
    elif args.command == "blueprints":
        run_blueprints()
    elif args.command == "monitor":
        run_monitor()
    elif args.command == "audit":
        run_audit(firewall=args.firewall, antivirus=args.antivirus, policies=args.policies)
    elif args.command == "orchestrate":
        run_orchestration(args.agents)
    elif args.command == "tasks":
        run_tasks(agent_filters=args.agent, status=args.status, csv_path=args.csv)
    else:  # pragma: no cover - defensive default
        parser.error(f"Unknown command: {args.command}")


if __name__ == "__main__":  # pragma: no cover - module entry point
    main()
