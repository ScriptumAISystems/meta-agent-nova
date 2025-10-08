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
from .system.containers import inspect_container_runtimes, log_container_report
from .blueprints.generator import create_blueprint, list_available_blueprints
from .monitoring.alerts import (
    DEFAULT_THRESHOLDS_PATH,
    execute_alert_workflow,
    notify_info,
    notify_warning,
)
from .monitoring.dashboards import (
    export_lux_compliance_slice,
    export_migration_dashboard,
)
from .monitoring.logging import configure_logger, log_error, log_info, log_warning
from .monitoring.reports import build_markdown_test_report
from .system.roadmap import (
    build_global_step_plan,
    build_next_steps_summary,
    build_phase_roadmap,
)
from .system.tasks import (
    build_markdown_task_overview,
    build_stepwise_task_checklist,
    filter_tasks as filter_agent_tasks,
    load_agent_tasks,
    normalise_agent_identifier,
    resolve_task_csv_path,
)
from .system.progress import build_progress_report


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
    dashboard_path = export_migration_dashboard()
    log_info(f"Grafana dashboard exported to {dashboard_path}")
    lux_path = export_lux_compliance_slice()
    log_info(f"LUX compliance slice exported to {lux_path}")
    notify_warning("Monitoring is running in stub mode.")
    notify_info("No active alerts.")


def run_alerts(
    thresholds: Path | None = None,
    snapshot: Path | None = None,
    *,
    dry_run: bool = False,
    export: Path | None = None,
) -> None:
    """Evaluate KPI thresholds and optionally export a journal report."""

    configure_logger()
    thresholds_path = thresholds or DEFAULT_THRESHOLDS_PATH
    events = execute_alert_workflow(
        thresholds_path=thresholds_path,
        snapshot_path=snapshot,
        dry_run=dry_run,
        export_path=export,
    )
    if events:
        log_info(f"Alert evaluation generated {len(events)} Ereignis(se).")
    else:
        log_info("Alert evaluation reported no threshold breaches.")


def run_containers(kubeconfig: Path | None = None) -> None:
    """Inspect Docker and Kubernetes availability and log the findings."""

    configure_logger()
    report = inspect_container_runtimes(kubeconfig=kubeconfig)
    log_container_report(report)


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
    *,
    as_checklist: bool = False,
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

    if as_checklist:
        overview = build_stepwise_task_checklist(filtered_tasks)
    else:
        overview = build_markdown_task_overview(filtered_tasks)
    for line in overview.splitlines():
        log_info(line)


def run_roadmap(csv_path: Path | None = None, phases: Iterable[str] | None = None) -> None:
    """Render the execution roadmap with step-by-step guidance."""

    configure_logger()
    resolved_path = resolve_task_csv_path(csv_path)
    log_info(f"Loading agent tasks from {resolved_path}")

    try:
        tasks = load_agent_tasks(resolved_path)
    except FileNotFoundError as exc:
        log_error(f"Task overview file not found: {exc}")
        raise

    roadmap = build_phase_roadmap(tasks, phase_filters=phases)
    for line in roadmap.splitlines():
        log_info(line)


def run_next_steps(
    csv_path: Path | None = None,
    *,
    limit_per_agent: int = 1,
) -> None:
    """Render the next-step summary derived from pending tasks."""

    configure_logger()
    resolved_path = resolve_task_csv_path(csv_path)
    log_info(f"Loading agent tasks from {resolved_path}")

    try:
        tasks = load_agent_tasks(resolved_path)
    except FileNotFoundError as exc:
        log_error(f"Task overview file not found: {exc}")
        raise

    summary = build_next_steps_summary(tasks, limit_per_agent=limit_per_agent)
    for line in summary.splitlines():
        log_info(line)


def run_step_plan(
    csv_path: Path | None = None,
    phases: Iterable[str] | None = None,
) -> None:
    """Render the complete step-by-step plan across phases."""

    configure_logger()
    resolved_path = resolve_task_csv_path(csv_path)
    log_info(f"Loading agent tasks from {resolved_path}")

    try:
        tasks = load_agent_tasks(resolved_path)
    except FileNotFoundError as exc:
        log_error(f"Task overview file not found: {exc}")
        raise

    plan = build_global_step_plan(tasks, phase_filters=phases)
    for line in plan.splitlines():
        log_info(line)


def run_progress(
    csv_path: Path | None = None,
    agent_filters: Iterable[str] | None = None,
    *,
    pending_limit: int | None = None,
) -> None:
    """Render the aggregated progress snapshot."""

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
    filtered_tasks = filter_agent_tasks(tasks, filters, None)
    if not filtered_tasks:
        log_warning("No tasks matched the provided filters.")
        return

    report = build_progress_report(filtered_tasks, pending_limit=pending_limit)
    for line in report.splitlines():
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

    alerts_parser = subparsers.add_parser(
        "alerts", help="Evaluate KPI thresholds and emit PagerDuty/webhook events"
    )
    alerts_parser.add_argument(
        "--thresholds",
        type=Path,
        metavar="PATH",
        help="Optional path to a custom threshold definition file.",
    )
    alerts_parser.add_argument(
        "--snapshot",
        type=Path,
        metavar="PATH",
        help="Path to a KPI snapshot (JSON or YAML). Required unless --dry-run is used.",
    )
    alerts_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate synthetic snapshot data and avoid dispatching real alerts.",
    )
    alerts_parser.add_argument(
        "--export",
        type=Path,
        metavar="PATH",
        help="Optional path for exporting a Markdown alert summary for the journal.",
    )

    containers_parser = subparsers.add_parser(
        "containers", help="Prüfe Docker- und Kubernetes-Laufzeitumgebungen"
    )
    containers_parser.add_argument(
        "--kubeconfig",
        type=Path,
        metavar="PATH",
        help="Optionaler Pfad zu einer Kubeconfig-Datei, die bevorzugt geprüft werden soll.",
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
    tasks_parser.add_argument(
        "--checklist",
        action="store_true",
        help="Render the task overview as a step-by-step checklist.",
    )

    roadmap_parser = subparsers.add_parser(
        "roadmap", help="Display the phased roadmap and remaining steps"
    )
    roadmap_parser.add_argument(
        "--csv",
        type=Path,
        metavar="PATH",
        help="Optional path to an alternative task overview CSV file.",
    )
    roadmap_parser.add_argument(
        "--phase",
        nargs="*",
        metavar="PHASE",
        help="Limit the roadmap to the specified phases (e.g. foundation).",
    )

    next_steps_parser = subparsers.add_parser(
        "next-steps",
        help="Display the next pending steps per agent",
    )
    next_steps_parser.add_argument(
        "--csv",
        type=Path,
        metavar="PATH",
        help="Optional path to an alternative task overview CSV file.",
    )
    next_steps_parser.add_argument(
        "--limit",
        type=int,
        metavar="N",
        default=1,
        help="Number of steps to show per agent (use 0 for unlimited).",
    )

    step_plan_parser = subparsers.add_parser(
        "step-plan",
        help="Display the complete step-by-step execution plan",
    )
    step_plan_parser.add_argument(
        "--csv",
        type=Path,
        metavar="PATH",
        help="Optional path to an alternative task overview CSV file.",
    )
    step_plan_parser.add_argument(
        "--phase",
        nargs="*",
        metavar="PHASE",
        help="Limit the plan to the specified phases (e.g. observability).",
    )

    progress_parser = subparsers.add_parser(
        "progress",
        help="Display the overall progress snapshot",
    )
    progress_parser.add_argument(
        "--csv",
        type=Path,
        metavar="PATH",
        help="Optional path to an alternative task overview CSV file.",
    )
    progress_parser.add_argument(
        "--agent",
        nargs="*",
        metavar="AGENT",
        help="Filter the progress report by agent identifier (e.g. nova, orion).",
    )
    progress_parser.add_argument(
        "--limit",
        type=int,
        metavar="N",
        default=None,
        help=(
            "Number of pending tasks to show per agent (omit or 0 for unlimited)."
        ),
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
    elif args.command == "alerts":
        run_alerts(
            thresholds=args.thresholds,
            snapshot=args.snapshot,
            dry_run=args.dry_run,
            export=args.export,
        )
    elif args.command == "containers":
        run_containers(kubeconfig=args.kubeconfig)
    elif args.command == "audit":
        run_audit(firewall=args.firewall, antivirus=args.antivirus, policies=args.policies)
    elif args.command == "orchestrate":
        run_orchestration(args.agents)
    elif args.command == "tasks":
        run_tasks(
            agent_filters=args.agent,
            status=args.status,
            csv_path=args.csv,
            as_checklist=args.checklist,
        )
    elif args.command == "roadmap":
        run_roadmap(csv_path=args.csv, phases=args.phase)
    elif args.command == "next-steps":
        run_next_steps(csv_path=args.csv, limit_per_agent=args.limit)
    elif args.command == "step-plan":
        run_step_plan(csv_path=args.csv, phases=args.phase)
    elif args.command == "progress":
        run_progress(
            csv_path=args.csv,
            agent_filters=args.agent,
            pending_limit=args.limit,
        )
    else:  # pragma: no cover - defensive default
        parser.error(f"Unknown command: {args.command}")


if __name__ == "__main__":  # pragma: no cover - module entry point
    main()
