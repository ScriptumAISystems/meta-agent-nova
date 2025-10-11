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
- **Task Automation**: gRPC-based task queue with persistence, KPI tracking and audit trails for deterministic background work.
- **Governance & Security**: OPA-powered policy engine, ISO 27001 aligned auditing and compliance registry for operational transparency.

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
- `containers`: verify Docker/Kubernetes availability and kubeconfig presence.
- `network`: generate the VPN rollout plan (WireGuard/OpenVPN) and optionally export it as Markdown documentation.
- `backup`: render the backup & recovery rollout plan (default playbook) and optionally export it as Markdown documentation.
- `orchestrate`: execute every registered agent sequentially using the blueprint specifications. Provide ``--agents`` to limit the set and use ``NOVA_EXECUTION_MODE=parallel`` (or the programmatic API) for concurrent execution.
- `tasks`: inspect agent assignments or render them as a checklist with ``--checklist``.
- `roadmap`: create a phase-orientated progress report that highlights the remaining steps for each specialist. Pass `--phase foundation observability` to focus on specific phases.
- `next-steps`: show the wichtigsten To-dos je Agent mit optionaler Begrenzung über `--limit`; kombiniere mit `--phase`, um nur ausgewählte Phasen einzublenden.
- `step-plan`: render an ordered Schritt-für-Schritt-Plan über alle offenen Aufgaben; combine with `--phase` to narrow the focus.
- `progress`: generate an aggregated Fortschrittsbericht with per-agent snapshots and the next pending steps (optionally cap the previews with `--limit`; by default all open To-dos are shown; focus on specific specialists via `--agent`).
- `summary`: produce a kompakte Roadmap-Zusammenfassung mit Phasenfortschritt und den wichtigsten nächsten Aufgaben je Agent (limitierbar über `--limit`).

Example workflow:

```bash
python -m nova setup --packages docker kubernetes
python -m nova blueprints
python -m nova orchestrate
python -m nova roadmap
python -m nova step-plan
python -m nova progress
python -m nova network --vpn wireguard --export orchestration_journal/vpn/wireguard_plan.md
python -m nova backup --plan default --export orchestration_journal/backups/default_plan.md
```

## Task Queue & Microservices

- `nova.task_queue`: gRPC microservice backed by pluggable persistence (SQLite default, Redis for distributed deployments). It supports reliable enqueue/dequeue semantics, worker acknowledgements, health heartbeats and structured metadata.
- Components can communicate through the generated gRPC stub (`TaskQueueStub`) and can run inside Kubernetes or standalone containers.
- Unit tests (`tests/test_task_queue.py`, `tests/test_task_queue_redis.py`) demonstrate the end-to-end lifecycle across both persistence backends to help onboard new contributors quickly.
- Production deployments should install the optional `redis` Python package when targeting a managed Redis instance; local tests can rely on the built-in in-memory stub.

## Policy Engine & Authorization

- `nova.policy.PolicyEngine` communicates with an Open Policy Agent (OPA) control plane using the standard REST API.
- Policies can be authored in Rego (`nova/policy/policies/authorization.rego`) and hot-reloaded in OPA.
- Cached decisions reduce load on OPA while keeping results auditable through structured logging.

## Monitoring, KPIs & Logging

- `nova.logging.initialize_logging` configures structured logging with rotation-ready handlers.
- `nova.logging.kpi.KPITracker` captures counters and latency statistics for operational dashboards.
- Every subsystem emits KPI snapshots and audit trails so that incidents can be reconstructed quickly.

## Security & Compliance

- `nova.security` contains audit storage (`AuditStore`), runtime logging helpers (`AuditLogger`) and an ISO 27001 compliance registry.
- The `SecurityManager` centralises registration of controls and connects operational events with their audit trail.
- All code paths follow least-privilege defaults: policy decisions deny by default, and task queue metadata is validated at ingress.

## Roadmap

- Finalise feature list for v1.0. ✅ (See `docs/v1_feature_list.md`.)
- Develop agent blueprints and roles. ✅
- Implement test harness and monitoring. ✅
- Prepare migration to Spark hardware. ✅ (See `docs/SPARK_MIGRATION_PLAN.md`.)
- Schedule early integration and security reviews for each milestone to minimise rework. ✅ (See `docs/INTEGRATION_SECURITY_REVIEWS.md`.)
- Extend roadmap milestones with a "Definition of Done" per agent role to keep progress measurable. ✅ (See `docs/DEFINITION_OF_DONE.md` and the binary contract in `docs/NOVA_DEFINITION_OF_DONE.md`.)
- Refine automated testing and monitoring pipelines in parallel to maintain endgame stability. ✅ (See `docs/TESTING_MONITORING_REFINEMENT.md`.)

## Contributing

Contributions and feedback are welcome. Please open issues or pull requests to discuss changes.
