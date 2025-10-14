# Post-Roadmap Operations Checklist

> Status: Roadmap abgeschlossen (100 %), produktive Betriebsfreigabe ausstehend.

## 1. Definition-of-Done Validierung
- [ ] **Nova – Gesamtprojektleitung**
  - Alle Artefakte in `docs/FOUNDATION_*.md` und `orchestration_journal/updates/` mit finalem Freigabestatus versehen.
  - Backup- und VPN-Pläne gegen aktuelle Infrastrukturparameter prüfen.
- [ ] **Orion – KI-Software**
  - Validierungsprotokolle für Finetuning (`orchestration_journal/models/`) gegen Produktionsdatenbestand abgleichen.
  - Letzten Modell-Build signieren und im Registry-Katalog vermerken.
- [ ] **Lumina – Daten & Speicher**
  - Vector-Ingest (`nova/task_queue/vector_ingest.py`) in Staging durchlaufen lassen und Logs archivieren.
  - Dateninventar (`orchestration_journal/data/`) auf DSGVO-konforme Freigaben prüfen.
- [ ] **Echo – Experience & Avatar**
  - Avatar-Pipeline (`docs/diagrams/avatar_pipeline.drawio`) anhand aktueller Assets testen.
  - Audio-/Video-Assets mit Qualitätsprotokollen (`orchestration_journal/experience/`) abzeichnen.
- [ ] **Chronos – Automatisierung**
  - n8n-Workflows (`orchestration_journal/automation/`) im Dry-Run bestätigen und Release-Tags setzen.
  - Bridge-Service (`deploy/automation/bridge/`) auf letzte Commit-Version verifizieren.
- [ ] **Aura – Monitoring**
  - Grafana-Dashboards (`docs/dashboards/`) an produktive KPIs anpassen.
  - Alerting-Runbooks (`orchestration_journal/monitoring/`) mit Incident-Response-Plan verlinken.

## 2. Go-Live Governance
- [ ] Formale Freigabeentscheidung im Lenkungsausschuss protokollieren.
- [ ] Security- & Datenschutz-Review-Ergebnisse (`docs/INTEGRATION_SECURITY_REVIEWS.md`) gegen Freigabestand prüfen.
- [ ] Betriebskonzept mit Verantwortlichkeiten und Eskalationsmatrix aktualisieren.

## 3. Übergabe & Inbetriebnahme
- [ ] Onboarding-Paket für Betriebsteam (inkl. CLI-Guides `python -m nova *`) paketieren.
- [ ] Übergabemeeting terminieren, Protokoll im Orchestrierungstagebuch dokumentieren.
- [ ] Service-Runbooks in `orchestration_journal/` auf neue Kontaktstellen aktualisieren.

## 4. Früher Betrieb & Monitoring
- [ ] Erste 14 Tage: Tägliche Health-Checks via `python -m nova summary` dokumentieren.
- [ ] Beobachtungsliste für bekannte Risiken (Modell-Drift, Datenlatenz) pflegen.
- [ ] Feedback-Loop mit Stakeholdern (UX, Support) aufsetzen und Ergebnisse wöchentlich reporten.
