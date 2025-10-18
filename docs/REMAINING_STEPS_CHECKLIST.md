# Offene Schritte nach Roadmap-Abschluss

Auch wenn alle Roadmap-Meilensteine als erledigt markiert sind, bleiben einige verbindliche Abschlussaufgaben übrig. Die folgende Checkliste verdichtet die offenen Punkte aus `docs/DEFINITION_OF_DONE.md`, `docs/NOVA_DEFINITION_OF_DONE.md` und den Übergabeanforderungen im Repository.

## 1. Definition-of-Done je Agentenrolle abschließen
- [ ] Nova: Binäre DoD-Kriterien aus `docs/NOVA_DEFINITION_OF_DONE.md` belegen (Health-Checks, Watchdog, Drift-Alerts, Auto-Rollback, Sophia-Kommunikation, Observability, Security, DX).
  - Gap-Analyse & Prioritäten dokumentiert unter `docs/DOD_VALIDATION_GAP_ANALYSIS.md` (Abschnitt Nova).
- [ ] Orion: Finetuning-Playbook aus `orchestration_journal/models/finetune_runbook.md` in die Praxis überführen, Referenz-LLM bereitstellen, LangChain-Integration testen.
  - Offene Validierungsschritte siehe `docs/DOD_VALIDATION_GAP_ANALYSIS.md` (Abschnitt Orion).
- [ ] Lumina: Datenbank-Deployments (MongoDB/PostgreSQL) und Vector-DB-Aufbau aus `docs/LUMINA_PLANS.md` validieren, Backup/Restore-Dry-Runs protokollieren.
  - Priorisierte Aufgaben laut `docs/DOD_VALIDATION_GAP_ANALYSIS.md` (Abschnitt Lumina).
- [ ] Echo: Avatar-Pipeline-End-to-End-Test auf Basis der ACE-Runbooks durchführen (Audio2Face/Riva) und Qualitätsmetriken dokumentieren.
  - Offene Nachweise zusammengefasst in `docs/DOD_VALIDATION_GAP_ANALYSIS.md` (Abschnitt Echo).
- [ ] Chronos: n8n-Automationen mit der LangChain-Bridge (`nova/automation/bridge.py`) in Betrieb nehmen, Data-Flywheel-KPIs monitoren.
  - Deploy- und Monitoring-Lücken siehe `docs/DOD_VALIDATION_GAP_ANALYSIS.md` (Abschnitt Chronos).
- [ ] Aura: Grafana-Stack (`deploy/monitoring/grafana-stack.yml`) produktionsreif machen, emotionale KPI-Visualisierung samt Datenschutzfreigabe nachweisen.
  - Aufgaben priorisiert in `docs/DOD_VALIDATION_GAP_ANALYSIS.md` (Abschnitt Aura).

## 2. Betriebsnachweise einsammeln
- [ ] Ergebnisse der automatisierten Tests (z. B. `tests/test_bridge_service.py`, `tests/test_vector_ingest.py`) erneut ausführen und in einem Übergabeprotokoll verlinken.
- [ ] Backup- und Recovery-Pläne (`orchestration_journal/backups/*.md`) durch Proberestore verifizieren.
- [ ] Sicherheits- und VPN-Protokolle (`orchestration_journal/vpn/wireguard_plan.md`) gegen aktuelle Infrastruktur spiegeln.

## 3. Go-Live & Übergabe vorbereiten
- [ ] Runbooks für Deploy/Rollback/Hotfix (siehe Anforderungen in `docs/NOVA_DEFINITION_OF_DONE.md`) finalisieren und in das Betriebswiki übernehmen.
- [ ] Service-Abnahme durch SRE/Compliance bestätigen lassen (Audit-Logs, Policy-Reports, Secret-Management-Nachweise).
- [ ] Go-Live-Freigabe-Meeting terminieren und Ergebnisse im Orchestrierungstagebuch dokumentieren.

> ✅ Sobald alle Kontrollkästchen abgehakt sind, gilt Nova auch nach Roadmap-Abschluss operativ als einsatzbereit.
