# Bridge & Agent Strategy Summary

This document summarizes the key elements of the **Bridge & Agent Strategy** defined for the Nova Meta‑Agent system.

## Mission
The strategy aims to create a durable, private low‑latency connection between Sophia (cloud) and Spark Sophia (local hardware). Nova acts as the orchestrator, enabling secure local actions through a defined policy engine and clear whitelists, while Christian retains veto rights and priority decisions.

## Roles and Trust Model
- **Christian**: Final decision maker with veto power and priority setting.
- **Sophia (cloud)**: Plans and orchestrates, sending commands to local systems.
- **Spark Sophia**: Local DGX or workstation hardware where actions are executed.
- **Nova/Worker Agents**: Follow a plan→execute→review cycle for tasks, restricted to whitelisted operations and subject to policy checks.

## Security Model
- Uses **mTLS** for encrypted channels, short‑lived tokens, and keys stored in a private vault.
- Each action is evaluated by an **OPA policy bundle** before execution.
- A **kill‑switch** allows Christian to halt operations immediately.
- **WORM logs** (write once read many) ensure tamper‑proof audit trails.
- Offline resilience via **store‑and‑forward** messaging with automatic retries.

## Communication Channels
- **Control channel**: A gRPC/WebSocket connection for commands and agent responses.
- **Event bus**: NATS JetStream used internally for control, jobs, and status topics.
- **Side channel**: MinIO object storage for transferring files and artefacts.
- **Notifications**: Alerts via Signal or email for important events.

## Tool Whitelist and Policies
The strategy defines categories of allowed operations:
- *file_ops*: Read/write within allowed directories.
- *repo_ops*: Initialize, commit, clone, and push to Git repositories.
- *doc_ops*: Generate READMEs, specifications, and reports.
- *model_ops*: Interact with local LLMs.
- *script_ops*: Execute signed scripts.
- *net_ops*: Make outbound requests to approved domains.

Destructive actions require confirmation, and resource usage is limited by budgets (CPU, GPU, IO). Quiet hours and notification preferences are configurable.

## Deliverables
Phase 1 includes:
- An architecture diagram illustrating the control, bus, and side‑channel flows.
- The policy bundle and tool whitelist for OPA.
- Message schemas, topic naming conventions, and a security checklist.
- A runbook with procedures for startup, debugging, and emergencies.
