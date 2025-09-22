import argparse
from .system.checks import check_cpu, check_gpu, check_network
from .system.setup import prepare_environment, install_packages, configure_os
from .blueprints.generator import list_available_blueprints, create_blueprint
from .monitoring.logging import configure_logger, log_info, log_warning, log_error
from .monitoring.alerts import send_alert, notify_warning, notify_critical



def run_setup():
    """Perform system setup and installation tasks (placeholder)."""
    configure_logger()
    log_info("Starting system setup")
    prepare_environment()
    install_packages()
    configure_os()
    cpu_ok = check_cpu()
    gpu_ok = check_gpu()
    network_ok = check_network()
    if cpu_ok and gpu_ok and network_ok:
        log_info("System setup completed successfully.")
    else:
        log_warning(f"System setup completed with issues: CPU {cpu_ok}, GPU {gpu_ok}, Network {network_ok}")


def run_blueprints():
    """Generate agent blueprints (placeholder)."""
    configure_logger()
    blueprints = list_available_blueprints()
    log_info("Available blueprints: " + ", ".join(blueprints))
    for agent_type in blueprints:
        blueprint = create_blueprint(agent_type)
        log_info(f"Generated blueprint for {agent_type}: {blueprint}")



def run_monitor():
    """Start monitoring services (placeholder)."""
    configure_logger()
    log_info("Monitoring started")
    notify_warning("Monitoring is running")



def main():

    parser = argparse.ArgumentParser(
        prog="nova",
        description="Meta-Agent Nova command line interface"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("setup", help="Perform system setup and installation tasks")
    subparsers.add_parser("blueprints", help="Generate agent blueprints")
    subparsers.add_parser("monitor", help="Start monitoring services")

    args = parser.parse_args()

    if args.command == "setup":
        run_setup()
    elif args.command == "blueprints":
        run_blueprints()
    elif args.command == "monitor":
        run_monitor()


if __name__ == "__main__":
    main()
