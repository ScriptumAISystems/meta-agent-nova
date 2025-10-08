# Automated Testing & Monitoring Refinement Plan

This plan addresses the roadmap milestone "Refine automated testing and monitoring pipelines in parallel to maintain endgame stability".
It extends the existing harness in `tests/` and the monitoring utilities under `nova/monitoring`.

## 1. Objectives

1. Expand unit and integration coverage for critical orchestrator paths.
2. Provide deterministic reporting and evidence export for governance reviews.
3. Tighten alerting thresholds and on-call visibility ahead of Spark deployment.

## 2. Workstreams & Owners

| Stream | Description | Owner | Target Week |
| --- | --- | --- | --- |
| Test Harness Hardening | Add regression suites for task queue (Redis + SQLite) and policy engine mocks. | Chronos | KW 26 |
| Performance Benchmarks | Automate GPU/CPU baseline runs on staging hardware and capture artefacts via KPI tracker. | Nova & Aura | KW 27 |
| Monitoring Dashboard Enhancements | Extend Grafana/LUX dashboards with migration KPIs and compliance snapshots. | Aura | KW 28 |
| Alerting Automation | Configure PagerDuty/webhook integration triggered by KPI threshold breaches. | Chronos | KW 28 |

## 3. Detailed Tasks

- [x] **Test Harness Hardening**
  - [x] Extend `tests/test_task_queue.py` with concurrency stress scenarios (1k jobs, 10 workers).
  - [x] Mirror scenarios for Redis backend in `tests/test_task_queue_redis.py` with configurable latency injection.
  - [x] Create `tests/test_policy_engine.py` to validate allow/deny caches and OPA fallback behaviour using fixtures.
- [ ] **Performance Benchmarks**
  - [x] Implement `nova.monitoring.benchmarks.run_spark_baseline()` to orchestrate GPU, CPU and network measurements.
  - [x] Store benchmark artefacts in `nova/logging/kpi` for reuse by dashboards and reports.
  - [ ] Document benchmark execution in `docs/SPARK_MIGRATION_PLAN.md` section 5 upon completion.
- [ ] **Monitoring Dashboard Enhancements**
  - [x] Add migration KPI panels (deployment duration, error budgets) to Grafana JSON definitions (`docs/dashboards/spark_migration_grafana.json`).
  - [ ] Generate a LUX dashboard slice for compliance evidence (audit trail coverage, policy drift).
  - [ ] Link dashboards to review schedule in `docs/INTEGRATION_SECURITY_REVIEWS.md`.
- [ ] **Alerting Automation**
  - [x] Define KPI thresholds inside `nova/logging/kpi/thresholds.yaml`.
  - [x] Wire KPI breaches to PagerDuty/webhook integration script under `nova/monitoring/alerts.py`.
  - [x] Simulate alert run via `python -m nova.monitoring.alerts --dry-run` and attach output to the orchestration journal (dry run mode now emits structured payload logs for inclusion).

## 4. Metrics & Reporting

- Coverage target: 85 % statements across `nova/task_queue`, `nova/security`, `nova/policy` by KW 27.
- Benchmark delta thresholds: GPU utilisation ±5 %, CPU load ±10 %, network throughput ±7 % against baseline.
- Alert response SLA: acknowledge within 5 minutes, resolve within 30 minutes during migration window.

## 5. Dependencies & Risks

- Requires Spark staging access (see `docs/SPARK_MIGRATION_PLAN.md` section 1).
- PagerDuty integration depends on security review approval (see `docs/INTEGRATION_SECURITY_REVIEWS.md`).
- Benchmark automation consumes GPU time; coordinate with Orion to avoid model training conflicts.

## 6. Checkpoints

- ✅ Kick-off alignment with Chronos & Aura completed (2024-06-11).
- 🔄 Coverage instrumentation PR pending (`pytest --cov` pipeline update by Chronos).
- 🔄 KPI threshold definitions awaiting security sign-off (target KW 26).
- ⏳ Benchmark module implementation scheduled to start KW 25 once staging hardware confirmed.
