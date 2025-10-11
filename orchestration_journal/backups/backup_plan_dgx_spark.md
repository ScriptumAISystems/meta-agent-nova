# DGX Spark Backup & Recovery Plan (Customized)

## 1. Inventarisierung & Schutzumfang
- **Compute & Orchestrierung**: DGX Spark Base OS (Ubuntu 22.04), Kubernetes Control Plane (kubeadm), Worker Nodes (GPU-Profile), Container Registry Credentials.
- **Netzwerk & Sicherheit**: WireGuard VPN, Firewall-Regeln, Jump-Host Konfigurationen, Secrets im Vault (`kv/dgx-spark/*`).
- **Persistente Daten**:
  - PostgreSQL (Agenten- und Workflow-Daten, Namespace `sophia-core`).
  - MongoDB (Konversations- & Sessionspeicher, Namespace `sophia-chat`).
  - VectorDB (FAISS + Pinecone Mirror) für Wissensabrufe.
  - Artefakt-Registry (MLflow, Hugging Face private space) für LLM-Checkpoints.
- **Geschäftsanforderungen**: RPO ≤ 15 Minuten für produktive Datenbanken, RTO ≤ 120 Minuten für Conversational Core, DSGVO-konforme Datenlöschung (Aufbewahrungsfristen siehe `docs/GOVERNANCE_DATA_POLICY.md`).

## 2. Speicherziele & Verschlüsselung
- **Primärer Storage**: MinIO Cluster (`s3://dgx-spark-backups/`) mit SSE-KMS (Vault Transit) und Lifecycle Policies.
- **Sekundärer Storage**: Wöchentlicher Export nach Offsite S3 (`s3://dgx-spark-dr/`), Cross-Account IAM mit MFA Delete.
- **Offline Kopien**: Quartalsweise LUKS-verschlüsselte Snapshot-Archive auf dedizierter NAS (`/mnt/backup-nas`).

## 3. Backup-Jobs & Zeitplan
| Komponente | Tooling | Frequenz | Aufbewahrung | Notizen |
| --- | --- | --- | --- | --- |
| Kubernetes Manifeste & Cluster State | Velero + Restic | Wöchentlich Voll, Täglich Diff | 30 Tage | Export `velero backup create spark-weekly`. |
| PostgreSQL (`sophia-core`) | `pg_dump` + WAL Archiving | Täglich Voll 02:00 UTC, WAL alle 5 Min | 35 Tage | WAL repliziert nach Offsite S3, Checksums via `sha256sum`. |
| MongoDB (`sophia-chat`) | `mongodump` + Point-in-Time | Täglich Voll 02:30 UTC | 28 Tage | Oplog Tail für PITR, Hash-Report in `orchestration_journal/backups/logs/mongo`. |
| VectorDB (FAISS) | Snapshot Script (`scripts/backups/faiss_snapshot.py`) | 2× täglich 03:00/15:00 UTC | 21 Tage | Snapshot + Metadata (`manifest.json`). |
| Pinecone Mirror | Pinecone Snapshot API | Täglich 03:15 UTC | 21 Tage | Offsite Replikation automatisch durch Pinecone. |
| LLM Artefakte | MLflow Artifact Export | Bei neuem Release | 180 Tage | Trigger via GitHub Action `release-backup.yml`. |
| Config & Secrets | Ansible Playbook `backup-config.yml` | Wöchentlich 04:00 UTC | 60 Tage | GPG-verschlüsselte Tarballs, Schlüsselrotation halbjährlich. |

## 4. Automatisierung & Orchestrierung
- CronJobs im Namespace `sophia-backups` definieren (`charts/backups/cronjobs.yaml`).
- GitHub Workflow `backups-nightly.yml` triggert `python -m nova backup --plan default --check` und lädt Logs als Artefakt.
- Secrets via Vault Agent Injector; Backup-Pods mounten temporäre Token (`role: backups-runner`).
- Erfolg/Fehlschlag wird in `nova.task_queue` registriert; fehlgeschlagene Jobs erzeugen automatisch ein Jira Ticket (`BACKUP-ALERT`).

## 5. Monitoring & Alerts
- Prometheus Exporter (`backup-metrics-exporter`) liefert: letzte Laufzeit, Dauer, Datenvolumen.
- Grafana Dashboard `DGX Spark – Resilience` mit KPIs (Backup Freshness, Restore Drill Status).
- Alerting über `python -m nova alerts --profile backups`:
  - Warnung bei > 26h ohne erfolgreiche Sicherung einer kritischen Komponente.
  - Critical Alert bei Restore-Test älter als 45 Tage.
- Nightly Report `python -m nova summary --limit 5 --export orchestration_journal/reports/nightly.md` ergänzt Backup-Sektion.

## 6. Restore-Drills
- **Monatlich (1. Montag)**: Komplett-Restore in Staging Namespace `sophia-drill` mit anonymisierten Daten.
- **Quartalsweise**: Desaster-Szenario (verlust kompletter DGX-Konfiguration) → Bare-Metal Restore über PXE-Image + Konfigurations-Playbook.
- **Beweisführung**: Ergebnisse werden in `orchestration_journal/backups/drills/YYYY-MM-DD.md` dokumentiert (Dauer, Beobachtungen, Tickets).
- Rollback-Runbook (`docs/RUNBOOK_BACKUP_ROLLBACK.md`) referenzieren.

## 7. Compliance & Audits
- Audit-Checklist in `docs/FOUNDATION_BACKUP_RECOVERY.md` abhaken, Unterschrift durch Security-Officer.
- Data Protection Impact Assessment (DPIA) aktualisieren bei neuen Datenquellen.
- Halbjährliche Überprüfung der Zugriffspolicies (Vault, S3 IAM, Kubernetes RBAC).

## 8. Übergabe & Kommunikation
- Statusmeldung im Weekly Report (`progress_report.md`) ergänzen.
- Onboarding-Paket aktualisieren (`docs/ONBOARDING_CHECKLIST.md`): Backup-Prozeduren, Eskalationsmatrix.
- Task in `Agenten_Aufgaben_Uebersicht.csv` auf **Abgeschlossen** setzen und `python -m nova progress` erneut laufen lassen, um Status zu spiegeln.
