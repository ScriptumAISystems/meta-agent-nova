# Documentation Overview

This file consolidates pointers to important documentation for the Meta‑Agent Nova project.

## Bridge & Agent Strategy
This document summarises the security, communication and governance model for Nova and the Spark Sophia ecosystem. It describes roles (Christian, Sophia, Spark Sophia, Nova/Worker agents), the trust model, mTLS connections, token rotation, Open Policy Agent (OPA) policies, a kill‑switch, WORM logging, offline robustness, and the whitelisted categories of operations (file ops, repo ops, doc ops, model ops, script ops and net ops). See `Bridge_Agent_Strategy_summary.md` for details.

## Agent Tasks Overview
This document summarises the tasks for each agent role — Nova, Orion, Lumina, Echo, Chronos and Aura — as extracted from the CSV file. Tasks include system setup, software installation, database configuration, avatar creation, workflow automation and monitoring/dashboards. See `Agenten_Aufgaben_Uebersicht_summary.md` for a full list.

## Tasks List
The file `TASKS.md` consolidates all tasks across agents into one location. Use this list to track progress and plan the implementation of Nova and its sub‑agents.

## v1.0 Feature Catalogue
`docs/v1_feature_list.md` captures the scoped feature set, owners and acceptance criteria for the v1.0 release. It serves as the reference when updating the roadmap and validating Definition-of-Done per agent role.

## Spark Hardware Migration Plan
`docs/SPARK_MIGRATION_PLAN.md` lists the checklists required to move Nova and its specialist agents from local validation to the Spark hardware clusters, covering environment readiness, security, deployment automation, data migration, observability and rollback.

## Orchestration Communication
`docs/ORCHESTRATION_REPORTS.md` explains how the communication hub records agent messages and how Markdown status reports are produced after each orchestration run.

## Execution Plan
`docs/EXECUTION_PLAN.md` details the new phased execution model that aligns the orchestrator with the responsibilities captured in `TASKS.md`. Each phase lists participating agents, goals and the broadcast messages emitted during orchestration.

## VPN & Remote Access Playbooks
`docs/FOUNDATION_VPN_SETUP.md` beschreibt Schritt 3 der Foundation-Phase und liefert detaillierte Rollout-Pläne für WireGuard und OpenVPN. Der Leitfaden erklärt Validierung, Härtung und die Integration in das Monitoring. Die Pläne lassen sich auch per CLI (`python -m nova network --vpn <typ> --export ...`) generieren.

## Task Coverage Summary
`docs/TASK_COMPLETION.md` cross-references every requirement from `TASKS.md` with the blueprint tasks executed during orchestration to simplify auditing and reporting.

Use these documents together to understand the project's context and to guide future development.
