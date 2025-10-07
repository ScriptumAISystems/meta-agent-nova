# Orchestration Communication & Reporting

The Nova orchestrator now exposes a communication hub that records every
message exchanged between agents and the orchestration engine. Each agent
publishes a status message when a task is completed. The orchestrator
also publishes lifecycle notifications before and after each agent run,
ensuring that pre-run instructions are visible to the agents.

All recorded messages are persisted in an in-memory log that becomes part
of the orchestration report. A Markdown summary can be generated via
`OrchestrationReport.to_markdown()` and is automatically logged by the CLI
(`python -m nova orchestrate`).

Key capabilities:

- Track per-task messages, including metadata about expected outputs and
  warnings.
- Deliver pre-run instructions and start signals to every agent, captured
  as part of the agent execution report to improve auditability.
- Filter the communication log for specific recipients, allowing agents
  such as monitoring or workflow services to pull only relevant updates.
- Produce Markdown summaries that can be copied into documentation or
  shared with stakeholders after each orchestration run.
- Run agents sequentially or in parallel by passing ``execution_mode`` to
  the orchestrator. Parallel mode uses a thread pool while maintaining
  deterministic ordering in the resulting reports.
- Generate ready-to-share QA/test documentation via
  :func:`nova.monitoring.reports.build_markdown_test_report`, which wraps
  the orchestration report in a stakeholder-friendly format.

This mechanism provides the foundation for richer coordination between
Nova, Lumina, Orion, Echo, Chronos and Aura while keeping the system fully
observable and auditable.

