# Nova Execution Plan

Nova coordinates six specialist agents across a staged execution plan. The
plan provides deterministic ordering, clear responsibilities and explicit
dependencies so that the orchestration engine can broadcast contextual
instructions before every phase begins. The default phases are:

1. **Foundation** – Led by Nova to validate infrastructure, container
   platforms, remote access, security audits and backup strategies.
2. **Model Operations** – Orion prepares the model toolchain while Chronos
   provisions automation workflows, CI/CD, LangChain/n8n pipelines and the
   data flywheel for continuous improvement.
3. **Data Services** – Lumina deploys MongoDB, PostgreSQL and the vector
   knowledge base required for Sophia.
4. **Experience** – Echo delivers the ACE stack, Omniverse avatar pipeline
   and Teams integration artefacts.
5. **Observability** – Aura activates Grafana, the LUX dashboard, energy
   optimisation insights and emotional feedback visualisations.

Each phase emits a ``phase-start`` broadcast that includes a description of
its goals and the participating agents. Agents receive ``agent-start``
messages enriched with dependency metadata, enabling them to review prior
phases before running their tasks. The orchestrator executes phases
sequentially or in parallel (per phase) while maintaining a predictable
report ordering.

The CLI persists an aggregated Markdown test report with the execution plan
under ``$NOVA_HOME/reports/nova-test-report.md`` after every orchestration
run. This document can be shared with stakeholders to evidence that all
tasks listed in ``TASKS.md`` are covered by the blueprints and simulated
executions.
