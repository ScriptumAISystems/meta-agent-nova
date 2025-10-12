# LUX KPI-Katalog

Dieser Katalog beschreibt die Kernmetriken für das LUX-Dashboard und verknüpft
sie mit Datenquellen und Verantwortlichkeiten.

| KPI | Beschreibung | Quelle | Owner | Schwellenwert |
| --- | --- | --- | --- | --- |
| Zufriedenheitsindex | Gewichtete Kombination aus CSAT, CES, NPS | n8n → PostgreSQL (`customer_feedback`) | Aura | ≥ 4.2 |
| Stimmung positiv (%) | Anteil positiver Sessions pro Tag | Vector-Ingest Report (`sentiment_score`) | Aura/Echo | ≥ 65 % |
| Energie pro Session (Wh) | Energieverbrauch DGX / Anzahl Sessions | Prometheus (`node_energy_seconds_total`) | Nova | ≤ 35 Wh |
| Antwortzeit P95 (s) | 95. Perzentil Zeit bis Antwortausspielung | Bridge Logs (OpenTelemetry) | Chronos | ≤ 2.5 s |
| Escalation Rate (%) | Anteil der Gespräche mit menschlicher Übergabe | n8n Workflow `summary-refresh` | Chronos | ≤ 8 % |
| Wissensabdeckung (%) | Trefferquote Vector Store Queries | `nova/task_queue/vector_ingest.py` Reports | Lumina | ≥ 92 % |

## Pflegeprozess

1. KPIs werden monatlich im Steering Committee überprüft.
2. Änderungen an Definitionen erfolgen via Pull Request gegen dieses Dokument.
3. Alerts werden in `nova/logging/kpi/thresholds.yaml` gespiegelt.

## Nächste Schritte

- [ ] Automatisierte Synchronisation der KPIs in Grafana Panels umsetzen.
- [ ] KPI-Drilldowns in `docs/dashboards/lux_dashboard.md` ergänzen.
