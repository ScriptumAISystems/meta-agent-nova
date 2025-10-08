# Definition of Done je Agentenrolle

Dieses Dokument konkretisiert die Qualitätskriterien, die erfüllt sein müssen, damit eine Agentenrolle als "done" gilt. Die Checklisten basieren auf den Aufgaben aus `TASKS.md`, dem v1.0 Feature-Katalog und den Roadmap-Meilensteinen.

## Gemeinsame Qualitätskriterien
- [ ] Dokumentation im Repository verlinkt (Readme, Playbooks, Automationsskripte).
- [ ] Automatisierte Tests oder Validierungsskripte für kritische Pfade vorhanden und ausgeführt.
- [ ] Sicherheits-, Logging- und Monitoring-Hooks aktiviert bzw. dokumentiert.
- [ ] Übergabeprotokoll mit Betriebs- bzw. Runbook-Hinweisen liegt vor.

## Nova – Chef-Agentin
- [ ] Hardware- und Systemaudits (CPU, GPU, Netzwerk, Speicher) dokumentiert, inkl. Pass/Fail-Report.
- [ ] Container- und Orchestrierungstools (Docker, Kubernetes) installiert, Versionen erfasst und Smoke-Test durchgeführt.
- [ ] VPN/Remote-Zugriff (WireGuard oder OpenVPN) konfiguriert, Zugangsdaten sicher abgelegt, Verbindungstest protokolliert.
- [ ] Sicherheits- und Backup-Strategie aktiv, inkl. Firewall-/OPA-Policies und Wiederherstellungsplan.
- [ ] `nova setup` Befehl bzw. Skripte liefern reproduzierbare Ergebnisse (CI-Check oder lokaler Dry-Run).

## Orion – KI-Software-Spezialist
- [ ] NVIDIA NeMo Installationsablauf dokumentiert, Abhängigkeiten geprüft (z. B. CUDA, cuDNN).
- [ ] Referenz-LLM bereitgestellt (z. B. Llama 3 oder Mixtral) mit Ressourcenprofil und Deployment-Beschreibung.
- [ ] Fine-Tuning-Konzept mit Datenschema, Evaluationsmetriken und Automatisierungspfad verabschiedet.
- [ ] LangChain/Agentframework-Integration nachgewiesen (Smoke-Test oder Beispielworkflow im Repository).
- [ ] Sicherheits- und Compliance-Aspekte (Lizenzierung, Datennutzung) bewertet und dokumentiert.

## Lumina – Database & Storage Expert
- [ ] MongoDB- und PostgreSQL-Deployments beschrieben (Installationsskripte oder Helm-Charts vorhanden).
- [ ] Backup- und Restore-Prozeduren für beide Datenbanken getestet und dokumentiert.
- [ ] Vektor-Datenbank (Pinecone, FAISS o. Ä.) ausgewählt, Benchmark-Ergebnisse und Integrationsschnittstelle vorhanden.
- [ ] Zugriffskontrollen (Benutzer, Rollen, Secrets) eingerichtet und überprüft.
- [ ] Monitoring- und Alerting-Checks für Datenbanken in Grafana/Prometheus integriert.

## Echo – Avatar & Interaction Designer
- [ ] NVIDIA ACE-Komponenten (Riva, Audio2Face, NeMo) installiert, Kompatibilität getestet.
- [ ] Avatar-Pipeline vom Modell bis zur Ausspielung dokumentiert (Sequenzdiagramm + Konfigurationsdateien).
- [ ] Animations- und Audioqualität anhand definierter KPIs gemessen (Latenz, FPS, Audio-Clarity).
- [ ] Integration in ausgewählte Kommunikationsplattform (z. B. Microsoft Teams) prototypisch umgesetzt.
- [ ] Datenschutz- und Content-Richtlinien für Audio/Video-Streams dokumentiert und abgenommen.

## Chronos – Workflow & Automation Specialist
- [ ] n8n-Instanz automatisiert aufsetzbar (Docker Compose, Helm oder Skript) und mit Beispiel-Workflows getestet.
- [ ] LangChain/n8n-Orchestrierung implementiert, inkl. Webhook/gRPC-Brücken und Fehlertoleranz-Strategie.
- [ ] CI/CD-Pipeline dokumentiert (GitHub Enterprise + Kubernetes) mit mindestens einem End-to-End-Durchlauf.
- [ ] Data-Flywheel Mechanismen definiert (Feedbackschleifen, Metriken) und im Monitoring sichtbar gemacht.
- [ ] Rollback- und Notfallprozesse für Automationen beschrieben und geübt.

## Aura – Monitoring & Dashboard Developer
- [ ] Grafana Deployment (lokal/Cluster) beschrieben, Dashboards versioniert und wiederholbar installierbar.
- [ ] LUX-Dashboard Mockups/Wireframes erstellt, mit Datenquellen aus `nova/logging/kpi` verdrahtet.
- [ ] KPI-Definitionen für Energie- und Ressourceneffizienz inklusive Alert-Grenzwerte dokumentiert.
- [ ] Emotionale/Stimmungs-Metriken konzipiert, Datenschutz implikationen bewertet und Freigabe eingeholt.
- [ ] Monitoring-Hooks (Logs, Metriken, Traces) in Testumgebung verifiziert.

> **Hinweis:** Fortschritt wird über Pull Requests nachvollzogen. Jede Rolle aktualisiert die Checkliste in Abstimmung mit den Roadmap-Meilensteinen und verlinkt die relevanten Artefakte.
