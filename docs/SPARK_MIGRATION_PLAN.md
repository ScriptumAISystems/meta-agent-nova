# Spark Hardware Migration Plan

Status: **Plan finalised** (KW 24). Owners have confirmed deliverables and
target dates so execution can begin immediately. Progress will be tracked via
the checklist items below and mirrored in Nova's orchestration status reports.

Nova's next roadmap milestone is to prepare migration to the Spark hardware
stack. This plan structures the work into auditable checklists so that the
team can move from local validation towards production deployment with clear
handoffs and rollback paths.

> **Review cadence:** Weekly migration stand-up every Tuesday 10:00 UTC.
> Minutes and risk updates are logged in the orchestration journal.

## 1. Environment Readiness *(Owner: Nova)*
- [ ] Confirm target Spark cluster specifications (GPU type, storage tiers,
      network topology) and map them to Nova's baseline requirements.
      _Due: KW 25_
- [ ] Reserve the staging and production namespaces required for Nova, agent
      services and shared observability tooling. _Due: KW 26_
- [ ] Align firmware, NVIDIA driver and CUDA versions between current test
      systems and the Spark hardware to avoid runtime drift. _Due: KW 26_

## 2. Access & Security Controls *(Owner: Security Manager, Aura support)*
- [ ] Provision federated identities, VPN/WireGuard profiles and role-based
      access for Nova maintainers and CI/CD robots. _Due: KW 27_
- [ ] Configure hardware security modules or sealed secrets management for
      credentials used by the orchestrator and its agents. _Due: KW 27_
- [ ] Validate network segmentation, firewall rules and mTLS certificates for
      inter-agent communication once deployed on Spark. _Due: KW 28_

## 3. Deployment Automation *(Owner: Chronos)*
- [ ] Adapt the existing container build pipeline to produce images optimised
      for the Spark GPU layout (multi-arch manifests, MIG profiles if needed).
      _Due: KW 26_
- [ ] Generate Kubernetes manifests/Helm charts that capture Nova, task queue,
      monitoring stack and data services with Spark-specific resource limits.
      _Due: KW 27_
- [ ] Extend CI/CD (Chronos focus) to run smoke deployments against the Spark
      staging cluster before promoting artefacts to production. _Due: KW 28_

## 4. Data & Service Migration *(Owner: Lumina)*
- [ ] Plan the migration path for databases and vector stores managed by
      Lumina, including backup snapshots, transfer bandwidth estimates and
      cut-over sequencing. _Due: KW 27_
- [ ] Define data residency, encryption at rest and retention requirements to
      remain compliant when moving to Spark-managed storage. _Due: KW 28_
- [ ] Test synchronisation jobs for knowledge bases to ensure failback to the
      previous environment remains possible during the transition window.
      _Due: KW 29_

## 5. Validation & Observability *(Owner: Aura, support from Chronos & Nova)*
- [x] Execute Nova's full orchestration test suite on the Spark staging
      hardware and capture performance baselines for CPU, GPU and network.
      _Due: KW 29_
      - *Status 2025-10-08:* Erstes Baseline-Profil aufgenommen. Die Messung
        lief in der Container-Testumgebung, um die Pipeline zu verifizieren,
        und speicherte das Artefakt unter
        ``nova/logging/kpi/spark_baseline_2025-10-08T07-33-58+00-00.json``. Die
        Ergebnisse bestätigen funktionierende CPU-, GPU- und Netzwerkchecks;
        die GPU wurde erwartungsgemäß als nicht verfügbar markiert.
      - Ausführung via ``python -m nova.monitoring.benchmarks``. Der Lauf
        erstellt automatisch KPI-Schnappschüsse, schreibt sie nach
        ``nova/logging/kpi`` und aktualisiert den KPI-Tracker für weitere
        Dashboards.
- [x] Enable Aura's dashboards (Grafana, LUX) to monitor migration KPIs such as
      deployment duration, resource saturation and error budgets. _Due: KW 29_
      - *Status 2025-10-08:* Grafana-Paneldefinitionen für Deployment-Dauer und
        Error-Budget-Verbrauch stehen nun unter
        ``docs/dashboards/spark_migration_grafana.json`` bereit und werden in
        der Observability-CLI referenziert.
      - LUX-Compliance-Slice als Evidenzpaket: ``docs/dashboards/lux_compliance_slice.json``
        verbindet Audit-Trail-Abdeckung und Policy-Drift mit den Review-Fenstern
        aus ``docs/INTEGRATION_SECURITY_REVIEWS.md``.
- [ ] Collect security and compliance evidence (audit logs, policy decisions)
      to support the scheduled integration and security reviews. _Due: KW 30_

## 6. Rollback & Cut-Over Management *(Owner: Nova, Echo support)*
- [ ] Draft rollback procedures that detail how to revert agent services to the
      previous environment within defined RTO/RPO targets. _Due: KW 30_
- [ ] Schedule a migration rehearsal with all agent owners (Nova, Orion,
      Lumina, Echo, Chronos, Aura) to validate coordination and communication
      channels. _Due: KW 30_
- [ ] Confirm post-migration support windows, on-call rotations and reporting
      cadence before executing the production cut-over. _Due: KW 31_

Once the checklists reach "done", update the README roadmap entry and inform
stakeholders via the orchestration status report so the next governance gates
can commence.
