# Orchestration Communication & Reporting

The Nova orchestrator now exposes a communication hub that records every
message exchanged between agents and the orchestration engine. Each agent
publishes a status message when a task is completed. The orchestrator
also publishes a final notification after an agent run finishes.

All recorded messages are persisted in an in-memory log that becomes part
of the orchestration report. A Markdown summary can be generated via
`OrchestrationReport.to_markdown()` and is automatically logged by the CLI
(`python -m nova orchestrate`).

Key capabilities:

- Track per-task messages, including metadata about expected outputs and
  warnings.
- Filter the communication log for specific recipients, allowing agents
  such as monitoring or workflow services to pull only relevant updates.
- Produce Markdown summaries that can be copied into documentation or
  shared with stakeholders after each orchestration run.

This mechanism provides the foundation for richer coordination between
Nova, Lumina, Orion, Echo, Chronos and Aura while keeping the system fully
observable and auditable.

