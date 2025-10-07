# Meta-Agent Nova

Meta-Agent Nova is a modular, autonomous agent orchestrator designed to configure, deploy and manage the Spark Sophia ecosystem and other multi-agent systems. Nova acts as the conductor that sets up hardware and software environments, provisions agent blueprints, monitors their health and automates routine maintenance.

## Mission

Nova's mission is to accelerate software delivery while improving reproducibility and safety. It provides a single command-line interface to prepare systems, install dependencies, generate agent blueprints and orchestrate multi-agent workflows. Every action is logged and auditable to ensure transparency.

## Features

- **Initial Setup**: Perform system checks for CPU, GPU and network, install required packages (Python, Docker, etc.), configure firewall and users.
- **Agent Blueprints**: Autogenerate 20–30 modular agent templates with predefined roles (planner, coder, tester, ops, etc.) and assign skills.
- **Orchestration & Monitoring**: Launch agent processes, run test simulations, monitor resource usage and automatically recover from errors. Runs can be executed sequentially or in parallel, depending on workload needs.
- **Execution Plan & Phase Coordination**: The orchestrator groups Nova, Orion, Lumina, Chronos, Echo and Aura into deterministic phases. Each phase emits broadcast instructions and dependency metadata (see `docs/EXECUTION_PLAN.md`).
- **Coordinated Communication**: Built-in communication hub captures inter-agent messages and produces Markdown status reports after every orchestration run.
- **Automated Test Reporting**: Generate distribution-ready QA summaries via ``nova.monitoring.reports.build_markdown_test_report`` to keep stakeholders informed.
- **Data Services Playbooks**: Ready-made deployment plans for MongoDB, PostgreSQL and vector stores live in ``docs/LUMINA_PLANS.md``.
- **Modularity & Portability**: All scripts and configurations are modular so the system can be migrated from a local machine to the Spark cluster.
- **User Interfaces**: Simple command-line interface (CLI) with optional web dashboard for status and control.
- **Logging**: Comprehensive logging and optional cloud backup of logs and configuration.

## Installation

Nova is currently under active development. For a local test run, ensure you have Python 3.10+ installed, then clone this repository and install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

After installation, you can start the manager with:

```bash
python -m nova --help
```

The CLI provides the following subcommands:

- `setup`: prepare the local Nova working directory, simulate package installation and run hardware checks.
- `blueprints`: list and preview the built-in agent blueprints.
- `monitor`: initialise the logging and alerting pipeline.
- `orchestrate`: execute every registered agent sequentially using the blueprint specifications. Provide ``--agents`` to limit the set and use ``NOVA_EXECUTION_MODE=parallel`` (or the programmatic API) for concurrent execution.

Example workflow:

```bash
python -m nova setup --packages docker kubernetes
python -m nova blueprints
python -m nova orchestrate
```

## Roadmap

- Finalise feature list for v1.0.
- Develop agent blueprints and roles. ✅
- Implement test harness and monitoring. ✅
- Prepare migration to Spark hardware.

## Contributing

Contributions and feedback are welcome. Please open issues or pull requests to discuss changes.
