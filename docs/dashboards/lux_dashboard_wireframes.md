# LUX Dashboard Wireframes

Die Wireframes beschreiben die geplante Struktur des LUX-Dashboards für Aura.
Jede Sektion verweist auf relevante Datenquellen und KPIs.

## 1. Executive Overview

- **Metriken**: Zufriedenheitsindex, Gesprächsanzahl, SLA-Erfüllung.
- **Visualisierung**: KPI-Karten oben, Trendlinie (30 Tage) darunter.
- **Quelle**: `nova/logging/kpi/lux_metrics.md`, `progress_report.md`.

## 2. Stimmungsanalyse

- Heatmap mit Stimmung pro Team/Zeitraum.
- Sentiment-Verteilung (positiv/neutral/negativ) als Donut.
- Datenquelle: Vector-Ingest Reports (`orchestration_journal/data/vector_ingest_report.md`).

## 3. Energie- & Ressourceneffizienz

- GPU/CPU-Auslastung (Prometheus), Energieverbrauch pro Session.
- Alerts: Schwellenwerte aus `nova/logging/kpi/thresholds.yaml`.
- KPI: Watt pro erfolgreicher Konversation.

## 4. Gesprächsfluss

- Sankey-Diagramm von Intent → Antworttyp.
- Zeitachsen-Analyse (Antwortzeit, Escalations).

## 5. Incident-Status

- Liste offener Incidents (`orchestration_journal/updates/incidents.md`).
- Drill-Down Links zu Runbooks (Nova, Orion, Chronos).

## Design-Notizen

- Farbpalette: Grafana `Midnight` Theme, Akzentfarben #5B8FF9, #61DDAA.
- Responsive Layout, optimiert für 1920x1080 Dashboards.
- Barrierefreiheit: Kontrastverhältnis ≥ 4.5:1.

## Nächste Schritte

1. Wireframes in Figma nachbauen und mit Stakeholdern abstimmen.
2. Panels im Grafana-Provisioning definieren (`deploy/monitoring/grafana/provisioning/dashboards/`).
3. Feedback-Schleife mit Echo zur Darstellung des Avatar-Stimmungsfeedbacks.
