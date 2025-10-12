# Grafana Deployment Notizen

Dieses Dokument protokolliert die vorbereitenden Schritte für Aura zur
Bereitstellung des Monitoring-Stacks (Prometheus, Grafana, Loki, Promtail).

## Setup-Schritte

1. `.env.monitoring` anlegen und Admin-Zugangsdaten hinterlegen:
   ```bash
   export GRAFANA_ADMIN_USER=aurora
   export GRAFANA_ADMIN_PASSWORD='***'
   ```
2. Compose-Stack starten:
   ```bash
   cd deploy/monitoring
   docker compose -f grafana-stack.yml up -d
   ```
3. Prometheus Targets prüfen (`http://localhost:9090/targets`).
4. Grafana anmelden (`http://localhost:3000`) und Datenquellen importieren
   (`prometheus`, `loki`).
5. Dashboard-JSON aus `docs/dashboards/lux_compliance_slice.json` importieren.

## Alerting

- Konfiguriere Kontaktpunkte für Teams (Webhook) und E-Mail.
- Thresholds aus `nova/logging/kpi/thresholds.yaml` übernehmen.
- Alert-Dry-Run: `python -m nova alerts --dry-run --export orchestration_journal/alerts.md`.

## Offene Tasks

- [ ] Provisioning-Dateien erstellen (`deploy/monitoring/grafana/provisioning/`).
- [ ] LUX-Dashboard Panels auf neue KPIs erweitern.
- [ ] Loki Retention Policy definieren (Standard 7 Tage → Ziel 30 Tage).

## Referenzen

- `docs/automation/data_flywheel_blueprint.md`
- `docs/dashboards/lux_dashboard.md`
- `progress_report.md` Abschnitt Aura
