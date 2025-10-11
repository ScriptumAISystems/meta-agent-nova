# Default Backup & Recovery Plan

## Zusammenfassung
Standardisierter Backup- und Wiederherstellungsplan für die Spark-Sophia-Umgebung. Der Plan deckt Systemkonfigurationen, Datenbanken, Modellartefakte und Arbeitsdaten ab und koppelt die Ergebnisse mit Novas Reporting.

## Schutzumfang & Ziele
- Wöchentliche Voll-Backups für Konfigurationsdateien (DGX, Kubernetes, VPN).
- Tägliche inkrementelle Sicherungen der produktiven Datenbanken (MongoDB, PostgreSQL).
- Snapshots der Vector-Datenbank sowie LLM-Checkpoints (NeMo/finetuning).
- Recovery Time Objective (RTO): < 2 Stunden für kritische Services.
- Recovery Point Objective (RPO): <= 15 Minuten für Transaktionsdaten.

## Backup-Jobs
- Konfigurations-Archive via `tar` in verschlüsseltem Object Storage (S3/MinIO) ablegen.
- Datenbank-Dumps automatisieren: `pg_dump` & `mongodump` inkl. Zeitstempel und Hash-Prüfsumme.
- Vector-Store Snapshots exportieren (`faiss`-Index oder Pinecone Snapshot) und mit Metadaten katalogisieren.
- LLM-Artefakte (Tokenizer, Adapter, LoRA-Gewichte) versionieren und in Artefakt-Registry replizieren.
- Backup-Logs nach `orchestration_journal/backups/` spiegeln und in `python -m nova alerts` einbinden.

## Recovery-Übungen
- Monatlicher Restore-Test auf isolierter Staging-Umgebung (inkl. Kubernetes-Namespace).
- Desaster-Szenario simulieren: Datenbank-Restore + LLM-Neustart mit dokumentiertem Zeitstempel.
- Netzwerk- und VPN-Konfigurationen aus Backup wiederherstellen und Tunnel-Konnektivität prüfen.
- Rollback-Plan für fehlgeschlagene Deployments dokumentieren (GitOps/Helm Releases).

## Validierung & Überwachung
- Checksummen-Vergleich (`sha256sum`) nach jedem Backup-Lauf.
- `python -m nova monitor`-KPIs erweitern: Backup-Dauer, Datenvolumen, letzte erfolgreiche Ausführung.
- Alert-Workflow mit `python -m nova alerts --dry-run` testen (Warnung bei >24h ohne Backup).
- Automatisierte Benachrichtigung an Security-Team bei fehlgeschlagenen Jobs.

## Aufbewahrung & Compliance
- 7 tägliche Inkrementals, 4 wöchentliche Voll-Backups, 12 Monatsarchive.
- Revisionssichere Ablage (WORM) für Compliance-relevante Daten (DSGVO/ISO 27001).
- Löschkonzept für personenbezogene Daten dokumentieren und jährlich überprüfen.

## Automatisierung & Integration
- Backup-Jobs via `cron` oder Argo Workflows orchestrieren; Status in Nova Task Queue spiegeln.
- CI/CD-Pipeline erweitert fehlgeschlagene Backups um automatische Ticket-Erstellung.
- Secrets (S3 Credentials, DB-User) im Vault verwalten und Rotation halbjährlich erzwingen.

## Nova-spezifische Hinweise
- Ergebnisse im Orchestrierungstagebuch unter `orchestration_journal/backups/` versionieren.
- Status der Aufgabenliste (`Agenten_Aufgaben_Uebersicht.csv`) nach erfolgreichem Drill aktualisieren.
- Definition-of-Done für Nova in `docs/DEFINITION_OF_DONE.md` abhaken, sobald Restore-Probe erfolgreich.
