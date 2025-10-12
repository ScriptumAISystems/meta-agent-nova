# Data Flywheel Blueprint (Chronos)

Dieser Blueprint beschreibt, wie das Data-Flywheel für Sophia aufgebaut und in
Nova integriert wird. Er deckt Datenerfassung, Automatisierung und Monitoring
ab und verweist auf bestehende Artefakte im Repository.

## Ziele

- Kontinuierliches Einsammeln von Konversationsdaten mit Zustimmung.
- Automatisierte Auswertung zur Erkennung von Verbesserungsbedarf.
- Trigger für Finetuning, Wissensdatenbank-Aktualisierungen und Dashboard-Updates.

## Architekturkomponenten

1. **Event Ingestion** – n8n Webhook (`/hook/sophia-session`) nimmt Gespräche
   entgegen und persistiert Rohdaten in PostgreSQL (`deploy/databases/`).
2. **Normalization Worker** – Python Task (`nova/task_queue/vector_ingest.py`)
   erzeugt Embeddings & Metadaten und schreibt in den Vector Store.
3. **Feedback Analytics** – LangChain Chain analysiert Stimmungs- und
   Qualitätskennzahlen, Ergebnisse landen in `nova/logging/kpi/`.
4. **Trigger Engine** – GitHub Actions Workflow (`.github/workflows/flywheel.yml`)
   bewertet KPIs und stößt Finetuning oder Wissensupdates an.
5. **Dashboard Sync** – Grafana Panels werden über API aktualisiert
   (`deploy/monitoring/grafana-stack.yml`).

## Prozessfluss

1. Benutzerinteraktion → Telemetrie landet per n8n Webhook im Data Lake.
2. Batch-Job (stündlich) startet `python -m nova data --pipeline vector-ingest`.
3. Ergebnisse werden als Markdown-Report (`orchestration_journal/data/vector_ingest_report.md`)
   abgelegt und ins Monitoring weitergereicht.
4. KPI-Thresholds aus `nova/logging/kpi/thresholds.yaml` entscheiden über
   automatische Alerts (`python -m nova alerts`).
5. Bei erfüllten Kriterien erstellt Chronos Tickets für Orion/Lumina zur
   Modell- bzw. Wissensaktualisierung.

## Sicherheits- & Compliance-Aspekte

- Daten mit PII werden vor Speicherung pseudonymisiert (`privacy.redact()` Helper).
- Zugriff auf Rohdaten nur über Service-Accounts mit Audit-Logging.
- DSGVO-Einwilligungen in `orchestration_journal/data/consent_log.md` dokumentieren.

## Offene Aufgaben

- [ ] GitHub Actions Workflow erstellen.
- [ ] Redaktionsprozess für Human-in-the-Loop Feedback definieren.
- [ ] Automatisierte Reports (`python -m nova progress --export`) einbinden.

## Übergabe

- Blueprint im Projektboard verlinken.
- Knowledge Transfer Session mit Orion & Aura planen.
- Fortschritt im `progress_report.md` reflektieren.
