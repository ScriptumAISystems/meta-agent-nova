# Operative Arbeitspakete

Diese Übersicht übersetzt die Roadmap- und Next-Steps-Dokumente in konkrete Arbeitspakete. Jedes Paket enthält Zielsetzung,
Abnahmekriterien, konkrete Aktivitäten, Validierungsschritte und empfohlene Dokumentationsartefakte. Die Pakete sind je
Agentenrolle gruppiert und priorisiert. Checkboxen markieren empfohlene Reihenfolgen.

> 🔄 **Update-Hinweis:** Nach der Bearbeitung eines Pakets sollten `python -m nova progress` und die CSV `Agenten_Aufgaben_Uebersicht.csv`
> aktualisiert werden, damit Reports und Dashboards den realen Stand widerspiegeln.

## Nova – Foundation & Infrastruktur

### Paket N1 – Container-Basis (Docker & Kubernetes)
- [x] **Ziel:** Docker- und Kubernetes-Laufzeit bereitstellen und mit Nova-CLI validieren.
- **Deliverables:**
  - Ausgefüllter Installationsreport laut `docs/FOUNDATION_CONTAINER_SETUP.md`.
  - Export `orchestration_journal/container-report.md` mit ✅ Status.
  - Aktualisierte CSV-Zeile „Docker & Kubernetes-Cluster installieren“.
- **Aktivitäten:**
  1. Anleitung `docs/FOUNDATION_CONTAINER_SETUP.md` Schritt für Schritt durchgehen.
  2. Für Entwicklungsumgebung Kind-Cluster erzeugen (`kind create cluster --name nova-foundation`).
  3. Produktionsnah kubeadm-/k3s-Setup vorbereiten; Konfiguration in `orchestration_journal/container-fix.md` protokollieren.
  4. Validierung: `python -m nova containers --export orchestration_journal/container-report.md`.
  5. Erfolg über `docker run hello-world` und `kubectl get nodes` sichern.
- **Abnahme:** Alle Checks ✅, Report im Orchestrierungstagebuch verlinkt.

### Paket N2 – VPN & Remote Access
- [x] **Ziel:** Gesicherte Zugänge via WireGuard oder OpenVPN bereitstellen.
- **Deliverables:**
  - Konfigurationsdateien (`infrastructure/vpn/<env>.conf` oder Vault-Eintrag) und Betriebsanleitung.
  - Markdown-Report `orchestration_journal/network/vpn_status.md` mit Testprotokoll.
- **Aktivitäten:**
  1. Anleitung `docs/FOUNDATION_VPN_SETUP.md` nutzen und Parameter in `nova/system/network.py` hinterlegen.
  2. Keys/Certificates generieren, Peer-Definitionen dokumentieren.
  3. Verbindung testen (`python -m nova network --vpn wireguard --export orchestration_journal/network/vpn_status.md`).
  4. Firewall- und Routingregeln erfassen.
- **Abnahme:** Erfolgreicher Ping/SSH über VPN, Audit-Log im Journal.

### Paket N3 – Security & Datenschutz
- [x] **Ziel:** Security Controls für Firewall, Anti-Virus und OPA-Policies belegen.
- **Deliverables:**
  - Audit-Report `orchestration_journal/security/audit_<datum>.log`.
  - Aktualisierte Findings-Liste `orchestration_journal/security/findings.md`.
- **Aktivitäten:**
  1. `docs/FOUNDATION_SECURITY_AUDIT.md` befolgen.
  2. `python -m nova audit --firewall enabled --antivirus enabled --policies enabled` ausführen.
  3. Findings eskalieren, Remediation-Tickets erstellen.
  4. Alert-Dry-Run dokumentieren (`python -m nova alerts --dry-run --export orchestration_journal/alerts.md`).
- **Abnahme:** Audit-Report ohne offene Findings, Definition-of-Done Security erfüllt.

### Paket N4 – Backup & Recovery
- [x] **Ziel:** Wiederherstellungsfähige Sicherungen für Infrastruktur, Datenbanken und Modelle.
- **Deliverables:**
  - Backup-Plan `orchestration_journal/backups/backup_plan_default.md` (angepasst).
  - Restore-Drill-Protokoll `orchestration_journal/backups/drills/<datum>.md`.
- **Aktivitäten:**
  1. `docs/FOUNDATION_BACKUP_RECOVERY.md` durcharbeiten.
  2. Backup-Jobs für Kubernetes (Velero), Datenbanken (`pg_dump`, `mongodump`) und Artefakte konfigurieren.
  3. Monatlichen Restore-Test planen, Hash-Prüfungen dokumentieren.
  4. `python -m nova backup --plan default --export orchestration_journal/backups/backup_plan_default.md` aktualisieren.
- **Abnahme:** Restore-Drill erfolgreich, CSV-Status gesetzt.

## Orion – Model Operations

### Paket O1 – NVIDIA NeMo Installationspfad
- [x] **Ziel:** Reproduzierbare Installation von NeMo inkl. Abhängigkeiten.
- **Deliverables:**
  - Setup-Skript `orchestration_journal/model_ops/nemo_install.sh` oder Terraform/Ansible Playbook.
  - Validierungslog `orchestration_journal/model_ops/nemo_validation.md`.
- **Aktivitäten:**
  1. Anforderungen aus `docs/next_steps.md` Abschnitt „KI-Stack vorbereiten“ übernehmen.
  2. Container- oder Conda-Umgebung definieren; GPU-Support (CUDA Toolkit) dokumentieren.
  3. Test-Notebook/Script mit `nemo.collections.nlp` Beispiel laden.
  4. Ergebnisse via `python -m nova summary --agent orion` prüfen.
- **Abnahme:** NeMo-Testskript läuft fehlerfrei, Dependencies versioniert.

### Paket O2 – LLM Auswahl & Bereitstellung
- [x] **Ziel:** Arbeitsfähiges Basismodell inklusive Bereitstellungskonzept.
- **Deliverables:**
  - Entscheidungsdokument `orchestration_journal/model_ops/llm_selection.md` mit Kriterien.
  - Deployment-Manifest (Helm Chart, Compose oder Terraform) im Repo-Pfad `nova/agents/llm_deployment/` (falls neu, Ordner anlegen).
- **Aktivitäten:**
  1. Kandidaten (Llama 3, Mixtral, etc.) bewerten: Lizenz, Parameter, HW-Bedarf.
  2. Deployment-Optionen (HF Inference Endpoint, TensorRT-LLM, vLLM) vergleichen.
  3. Proof-of-Concept mit `python -m nova agents --llm-status` ergänzen.
- **Abnahme:** Dokumentierte Entscheidung + lauffähige Bereitstellung in Testumgebung.

### Paket O3 – Fine-Tuning Blueprint
- [x] **Ziel:** Standardisierter Prozess für datengestütztes Finetuning.
- **Deliverables:**
  - Workflow-Diagramm `docs/diagrams/orion_finetuning_flow.png` (oder Markdown-Alternative).
  - Evaluationsplan `orchestration_journal/model_ops/finetuning_metrics.md`.
- **Aktivitäten:**
  1. Datenquellen inventarisieren, Annotationsstrategie skizzieren.
  2. Trainingspipeline (LoRA/PEFT) beschreiben; Parameter in YAML-Schablone hinterlegen.
  3. Automatisierte Tests definieren (`pytest` oder CLI `python -m nova qa --profile finetune`).
- **Abnahme:** Blueprint freigegeben, KPIs (BLEU, Rouge, Win-Rate) festgelegt.

## Lumina – Daten & Speicher

### Paket L1 – Datenbank-Automatisierung
- [x] **Ziel:** Automatisierte Bereitstellung von MongoDB & PostgreSQL.
- **Deliverables:**
  - Helm-Chart oder Compose-Datei `deploy/databases/docker-compose.yml`.
  - Betriebsdokumentation `orchestration_journal/data/db_operations.md`.
- **Aktivitäten:**
  1. Ports, Storage-Klassen, Backup-Hooks definieren.
  2. Healthchecks und Monitoring-Exporter (Prometheus) integrieren.
  3. `python -m nova monitoring --targets databases` für Smoke-Test ergänzen.
- **Abnahme:** Deployments laufen reproduzierbar, Monitoring liefert Metriken.

### Paket L2 – Wissensbasis / VectorDB
- [x] **Ziel:** Wissensdatenbank (FAISS oder Pinecone) mit ingest-/query-Flow.
- **Deliverables:**
  - Architekturnotiz `orchestration_journal/data/vector_architecture.md`.
  - Ingestion-Skript `nova/task_queue/vector_ingest.py` (falls neu, Implementierung hinzufügen) samt Unit-Tests.
- **Aktivitäten:**
  1. Kandidaten bewerten (Kosten, Latenz, Self-Hosting) und Entscheidung festhalten.
  2. Prototypische Pipeline: Dokumente -> Embeddings -> Index.
  3. Integrationstest `pytest tests/vector_ingest_test.py` (neu anlegen bei Bedarf).
- **Abnahme:** Query-Demo liefert Treffer, Dokumentation vollständig.

## Echo – Interaktionsdesign

### Paket E1 – ACE Stack Validierung
- [x] **Ziel:** Riva, Audio2Face und NeMo in funktionsfähigem Zusammenspiel.
- **Deliverables:**
  - Installationsmatrix `orchestration_journal/experience/ace_components.md`.
  - Testprotokoll `orchestration_journal/experience/ace_validation.log`.
- **Aktivitäten:**
  1. Container-Images identifizieren, Lizenzabhängigkeiten prüfen.
  2. Beispiel-Dialog über Riva (ASR → TTS) durchführen.
  3. Audio2Face-Szene mit Sample-Animation exportieren.
- **Abnahme:** End-to-End-Demo dokumentiert, offene Risiken aufgeführt.

### Paket E2 – Avatar Pipeline
- [x] **Ziel:** Dokumentierte Pipeline von Omniverse bis Teams/Frontend.
- **Deliverables:**
  - Sequenzdiagramm `docs/diagrams/avatar_pipeline.drawio`.
  - Betriebshandbuch `orchestration_journal/experience/avatar_runbook.md`.
- **Aktivitäten:**
  1. Omniverse-Szene definieren, Animations-Trigger festlegen.
  2. Audio2Face-Lip-Sync einbinden, Exportpfad zu Riva validieren.
  3. Teams/WebRTC-Integration planen (Auth, QoS, Bandbreite).
- **Abnahme:** Pipeline-Dokumentation vollständig, Integrationsrisiken adressiert.

## Chronos – Automatisierung & Workflow

### Paket C1 – n8n Grundinstallation
- [x] **Ziel:** Laufende n8n-Instanz mit Beispiel-Workflows.
- **Deliverables:**
  - Deployment-Skript `deploy/automation/n8n/docker-compose.yml` oder Kubernetes-Manifeste.
  - Workflow-Export `orchestration_journal/automation/n8n_sample_workflow.json`.
- **Aktivitäten:**
  1. Installationsanleitung (Docker/Kubernetes) dokumentieren.
  2. Beispiel-Workflow: Webhook → LangChain-Task → Slack/Teams Notification.
  3. Healthcheck-URL in Monitoring aufnehmen.
- **Abnahme:** Workflow lässt sich triggern, Logs liegen im Journal.

### Paket C2 – Data Flywheel & CI/CD
- [x] **Ziel:** Konzept für automatisiertes Feedback & Deployment.
- **Deliverables:**
  - Blueprint `docs/automation/data_flywheel_blueprint.md`.
  - CI/CD-Plan `orchestration_journal/automation/cicd_plan.md` (GitHub Enterprise + Kubernetes).
- **Aktivitäten:**
  1. Datenquellen für Feedback (User Logs, KPI) identifizieren.
  2. Automatisierte Retraining-Triggers definieren.
  3. Pipeline-Schritte (Lint, Tests, Deploy) festhalten; Github Actions/Vault-Integration beschreiben.
- **Abnahme:** Stakeholder sign-off, Tickets für Umsetzung erstellt.

## Aura – Monitoring & Dashboards

### Paket A1 – Grafana & Observability Stack
- [x] **Ziel:** Observability-Setup mit Prometheus/Grafana.
- **Deliverables:**
  - Deployment-Manifest `deploy/monitoring/grafana-stack.yml`.
  - Dashboard-Export `orchestration_journal/monitoring/grafana_dashboards.json`.
- **Aktivitäten:**
  1. Prometheus-Scrape-Targets definieren (Kubernetes, Datenbanken, LLM Service).
  2. Alerts in `python -m nova alerts` spiegeln.
  3. Zugriffskonzept und Nutzerrollen dokumentieren.
- **Abnahme:** Dashboards visualisieren Kernmetriken, Alerts getestet.

### Paket A2 – LUX Dashboard & Stimmungsanalyse
- [x] **Ziel:** UX-Mockups + Telemetrie-Anbindung für emotionales Feedback.
- **Deliverables:**
  - Wireframes `docs/dashboards/lux_dashboard_wireframes.pdf` (oder Markdown-Link).
  - KPI-Definition `nova/logging/kpi/lux_metrics.md`.
- **Aktivitäten:**
  1. Anforderungen aus Stakeholder-Interviews zusammentragen.
  2. Datenquellen (Sentiment-Analyse, Energieverbrauch) definieren.
  3. Prototypische Daten-Pipeline skizzieren (`nova/monitoring/ingest.py`).
- **Abnahme:** Wireframes abgestimmt, KPI-Katalog freigegeben.

---

### Arbeitsablauf & Governance
1. Wähle pro Sprint 2–3 Pakete mit höchster Priorität aus den Foundation-Bereichen.
2. Dokumentiere Fortschritte direkt im `orchestration_journal/`-Ordner.
3. Pflege Definition-of-Done (`docs/DEFINITION_OF_DONE.md`) und Roadmap (`README.md`) nach Abschluss.
4. Trigger Regressionstests (`pytest`, `python -m nova qa`) bevor neue Pakete gestartet werden.

Mit diesen Arbeitspaketen lassen sich die vorhandenen Planungsdokumente in konkrete, sofort ausführbare Aufgaben überführen.
