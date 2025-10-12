# LUX Dashboard – Monitoring Blueprint

Dieses Dokument sammelt Widgets, KPIs und Datenquellen für das zentrale Sophia
Dashboard. Ergänzungen erfolgen, sobald Aura die Observability-Phase startet.

## Kernbereiche

1. **Finetuning Telemetrie** – BLEU/ROUGE/Win-Rate, GPU-Auslastung, Checkpoint-Latenz.
2. **Workflow Status** – n8n Jobs, LangChain Bridge Events, Alerting.
3. **Emotion & Stimmung** – Voice Analytics, Sentiment Scores, Persona Feedback.

## Datenquellen

- Prometheus (Systemmetriken)
- PostgreSQL (n8n Workflow Logs)
- Object Storage Buckets (Checkpoint-Metadaten)
- LangChain Event Stream

## Offene Aufgaben

- [ ] Mock-Dashboard in Grafana anlegen.
- [ ] Datenquellen mit Service Accounts verknüpfen.
- [ ] KPI-Definition mit Stakeholdern finalisieren.
