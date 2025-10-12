# CI/CD Plan für Chronos

Dieser Plan beschreibt den Aufbau der GitHub Enterprise CI/CD-Pipeline für
Nova. Ziel ist eine reproduzierbare Auslieferung des LangChain Bridge Services,
der Datenpipelines sowie der Dashboards.

## Pipeline-Übersicht

1. **Lint & Unit Tests** – `pytest` (inkl. `tests/test_vector_ingest.py`) und
   `ruff` laufen bei jedem Pull Request.
2. **Container Build** – Docker Images für `bridge`, `n8n`, `vector-worker`
   werden gebaut und in die Registry `registry.internal/nova` gepusht.
3. **Integration Tests** – Compose-Stack (`deploy/automation/n8n/docker-compose.yml`)
   wird headless gestartet, Smoke-Test ruft n8n Webhook + Bridge API.
4. **Security Scans** – Trivy & Snyk prüfen Container und Dependencies.
5. **Deployment** – GitOps (Argo CD) aktualisiert Kubernetes-Cluster, Helm Chart
   `deploy/automation/bridge/chart/` liefert Rollouts.

## Rollen & Verantwortlichkeiten

- **Chronos** – Maintainer der Pipeline, überwacht Fehlermeldungen.
- **Orion** – Liefert Tests für Modell/Chain-Änderungen.
- **Lumina** – Pflegt Datenbank-Migrationsskripte (`deploy/databases/migrations/`).
- **Aura** – Validiert Monitoring-Hooks und Alert-Routing nach Deployments.

## Branching-Modell

- `main` → produktive Umgebung.
- `develop` → Staging, automatischer Deploy nach erfolgreicher Pipeline.
- Feature Branches → Pull Request Pflicht, require status checks.

## Artefakte & Logs

- Testreports als JUnit (`reports/junit/*.xml`).
- Coverage Report (`reports/coverage.xml`).
- Deployment Logs in `orchestration_journal/automation/deploy_logs/`.

## Offene To-dos

- [ ] GitHub Enterprise Runner bereitstellen.
- [ ] Secrets in HashiCorp Vault integrieren (`vault kv put cicd/...`).
- [ ] Canary-Deployment-Strategie für Bridge Service dokumentieren.

## Referenzen

- `docs/automation/data_flywheel_blueprint.md`
- `deploy/automation/bridge/README.md`
- `progress_report.md` (Abschnitt Chronos)
