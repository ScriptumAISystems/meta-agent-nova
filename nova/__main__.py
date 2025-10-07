"""Command line entry point for Meta-Agent Nova.

Provides a simple CLI with subcommands for system setup, blueprint generation
and monitoring utilities. The implementation is intentionally light-weight and
acts as a façade over the modules in :mod:`nova.system`, :mod:`nova.blueprints`
and :mod:`nova.monitoring`.
"""

from __future__ import annotations

import argparse
from typing import Iterable

from .system.checks import check_cpu, check_gpu, check_network
from .system.setup import configure_os, install_packages, prepare_environment
from .blueprints.generator import create_blueprint, list_available_blueprints
from .monitoring.alerts import notify_info, notify_warning
from .monitoring.logging import configure_logger, log_error, log_info, log_warning


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
        prepare_environment()
        package_list = list(packages) if packages is not None else DEFAULT_PACKAGES
        install_packages(package_list)
        configure_os()
    except Exception as exc:  # pragma: no cover - defensive logging
        log_error(f"System setup failed: {exc}")
        raise

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
        log_info(f"Generated blueprint for {agent_type}: {blueprint}")


def run_monitor() -> None:
    """Start monitoring services (placeholder)."""

    configure_logger()
    log_info("Monitoring services initialised.")
    notify_warning("Monitoring is running in stub mode.")
    notify_info("No active alerts.")


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
    else:  # pragma: no cover - defensive default
        parser.error(f"Unknown command: {args.command}")


if __name__ == "__main__":  # pragma: no cover - module entry point
    main()
