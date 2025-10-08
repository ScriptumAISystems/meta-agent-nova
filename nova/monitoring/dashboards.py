"""Utilities for provisioning Grafana dashboards used during the Spark migration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

_DEFAULT_DASHBOARD_PATH = (
    Path(__file__).resolve().parents[2] / "docs" / "dashboards" / "spark_migration_grafana.json"
)

_DEFAULT_LUX_SLICE_PATH = (
    Path(__file__).resolve().parents[2] / "docs" / "dashboards" / "lux_compliance_slice.json"
)


def _build_timeseries_panel(panel_id: int, *, environment_variable: str) -> dict[str, Any]:
    """Return the deployment duration panel configuration."""

    return {
        "id": panel_id,
        "type": "timeseries",
        "title": "Deployment Duration Trend",
        "datasource": {
            "type": "prometheus",
            "uid": "${DS_PROMETHEUS}",
        },
        "targets": [
            {
                "expr": (
                    "avg_over_time(nova_deployment_duration_seconds"
                    "{environment=\"${%s}\"}[24h])" % environment_variable
                ),
                "legendFormat": "Average",
                "refId": "A",
            },
            {
                "expr": (
                    "max_over_time(nova_deployment_duration_seconds"
                    "{environment=\"${%s}\"}[24h])" % environment_variable
                ),
                "legendFormat": "Max",
                "refId": "B",
            },
        ],
        "fieldConfig": {
            "defaults": {
                "unit": "s",
                "decimals": 2,
                "thresholds": {
                    "mode": "absolute",
                    "steps": [
                        {"color": "green", "value": None},
                        {"color": "yellow", "value": 900},
                        {"color": "red", "value": 1200},
                    ],
                },
            },
        },
        "options": {
            "legend": {"displayMode": "table"},
            "tooltip": {"mode": "multi"},
        },
        "gridPos": {"h": 9, "w": 24, "x": 0, "y": 0},
    }


def _build_error_budget_panel(panel_id: int, *, environment_variable: str) -> dict[str, Any]:
    """Return the error budget burn panel configuration."""

    return {
        "id": panel_id,
        "type": "stat",
        "title": "Error Budget Burn",
        "datasource": {
            "type": "prometheus",
            "uid": "${DS_PROMETHEUS}",
        },
        "targets": [
            {
                "expr": (
                    "(sum(nova_error_budget_consumed{environment=\"${%s}\"})"
                    " / sum(nova_error_budget_total{environment=\"${%s}\"}))"
                    " * 100"
                )
                % (environment_variable, environment_variable),
                "legendFormat": "Consumed",
                "refId": "A",
            }
        ],
        "fieldConfig": {
            "defaults": {
                "unit": "percent",
                "decimals": 1,
                "thresholds": {
                    "mode": "absolute",
                    "steps": [
                        {"color": "green", "value": None},
                        {"color": "yellow", "value": 50},
                        {"color": "red", "value": 85},
                    ],
                },
            }
        },
        "options": {
            "reduceOptions": {"calcs": ["lastNotNull"], "fields": ""},
            "orientation": "auto",
            "colorMode": "background",
            "graphMode": "none",
            "justifyMode": "center",
        },
        "gridPos": {"h": 6, "w": 12, "x": 0, "y": 9},
    }


def _build_remaining_budget_panel(panel_id: int, *, environment_variable: str) -> dict[str, Any]:
    """Return the remaining error budget trend panel configuration."""

    return {
        "id": panel_id,
        "type": "timeseries",
        "title": "Remaining Error Budget",
        "datasource": {
            "type": "prometheus",
            "uid": "${DS_PROMETHEUS}",
        },
        "targets": [
            {
                "expr": (
                    "sum_over_time(nova_error_budget_remaining"
                    "{environment=\"${%s}\"}[1d])" % environment_variable
                ),
                "legendFormat": "Remaining",
                "refId": "A",
            }
        ],
        "fieldConfig": {
            "defaults": {
                "unit": "percent",
                "thresholds": {
                    "mode": "absolute",
                    "steps": [
                        {"color": "red", "value": None},
                        {"color": "yellow", "value": 25},
                        {"color": "green", "value": 50},
                    ],
                },
            },
        },
        "options": {
            "legend": {"displayMode": "table"},
            "tooltip": {"mode": "single"},
        },
        "gridPos": {"h": 6, "w": 12, "x": 12, "y": 9},
    }


def build_migration_dashboard(*, refresh: str = "5m") -> dict[str, Any]:
    """Return the Grafana dashboard definition with migration KPI panels."""

    environment_variable = "Environment"
    panels = [
        _build_timeseries_panel(1, environment_variable=environment_variable),
        _build_error_budget_panel(2, environment_variable=environment_variable),
        _build_remaining_budget_panel(3, environment_variable=environment_variable),
    ]

    dashboard: dict[str, Any] = {
        "__inputs": [
            {
                "name": "DS_PROMETHEUS",
                "label": "Prometheus",
                "description": "Prometheus data source providing Nova KPI metrics.",
                "type": "datasource",
                "pluginId": "prometheus",
                "pluginName": "Prometheus",
            }
        ],
        "__requires": [
            {"type": "grafana", "id": "grafana", "name": "Grafana", "version": "9.5.0"},
            {
                "type": "panel",
                "id": "timeseries",
                "name": "Time series",
                "version": "9.5.0",
            },
            {"type": "panel", "id": "stat", "name": "Stat", "version": "9.5.0"},
        ],
        "annotations": {
            "list": [
                {
                    "builtIn": 1,
                    "datasource": {"type": "grafana", "uid": "-- Grafana --"},
                    "enable": True,
                    "hide": False,
                    "iconColor": "rgba(0, 211, 255, 1)",
                    "name": "Deployments",
                    "type": "dashboard",
                }
            ]
        },
        "description": "Observability snapshot used by Aura during the Spark migration.",
        "editable": True,
        "fiscalYearStartMonth": 1,
        "gnetId": None,
        "graphTooltip": 0,
        "id": None,
        "links": [],
        "liveNow": False,
        "panels": panels,
        "refresh": refresh,
        "schemaVersion": 38,
        "style": "dark",
        "tags": ["spark-migration", "nova", "aura"],
        "templating": {
            "list": [
                {
                    "name": environment_variable,
                    "type": "custom",
                    "label": "Environment",
                    "query": "staging,production",
                    "current": {"text": "staging", "value": "staging"},
                    "options": [
                        {"text": "staging", "value": "staging", "selected": True},
                        {"text": "production", "value": "production", "selected": False},
                    ],
                }
            ]
        },
        "time": {"from": "now-7d", "to": "now"},
        "timepicker": {"refresh_intervals": ["5m", "15m", "30m", "1h"]},
        "timezone": "",
        "title": "Spark Migration KPIs",
        "uid": "spark-migration-kpis",
        "version": 1,
        "weekStart": "",
    }
    return dashboard


def _build_widget_layout(widget_id: str, *, x: int, y: int, w: int, h: int) -> dict[str, int | str]:
    return {"widget": widget_id, "x": x, "y": y, "w": w, "h": h}


def build_lux_compliance_slice(
    *,
    review_windows: Iterable[str] | None = None,
    data_source: str = "nova-compliance-registry",
) -> dict[str, Any]:
    """Return the LUX dashboard slice used to evidence compliance metrics."""

    windows = list(review_windows) if review_windows is not None else [
        "KW 26 – Foundation Review",
        "KW 27 – Intelligence Review",
        "KW 28 – Interaction Review",
        "KW 31 – Cut-over Review",
    ]

    slice_payload: dict[str, Any] = {
        "id": "lux-compliance-evidence",
        "title": "Spark Migration Compliance Evidence",
        "description": (
            "Curated evidence package combining audit trail coverage, policy drift "
            "observability and review readiness for Spark migration governance."
        ),
        "data_sources": {
            "compliance_store": {
                "name": data_source,
                "type": "parquet",
                "path": "nova/security/compliance_store.parquet",
                "refresh_interval": "24h",
            },
            "policy_registry": {
                "name": "opa-policy-registry",
                "type": "json",
                "path": "nova/policy/cache/decision_log.json",
                "refresh_interval": "1h",
            },
        },
        "widgets": [
            {
                "id": "audit-trail-coverage",
                "type": "gauge",
                "title": "Audit Trail Coverage",
                "source": "compliance_store",
                "metric": "audit_trail.coverage",
                "format": "percent",
                "thresholds": {"warning": 90, "critical": 80},
                "description": "Share of orchestrated events backed by audit artefacts.",
            },
            {
                "id": "policy-drift-trend",
                "type": "sparkline",
                "title": "Policy Drift",
                "source": "policy_registry",
                "metric": "opa.policy_drift_score",
                "format": "ratio",
                "thresholds": {"warning": 0.2, "critical": 0.4},
                "description": "OPA decision drift compared to approved baselines (0 = aligned).",
            },
            {
                "id": "review-readiness",
                "type": "timeline",
                "title": "Review Readiness Checklist",
                "items": [
                    {
                        "label": window,
                        "status_metric": "audit_trail.coverage",
                        "acceptance_criteria": ">= 95% coverage",
                    }
                    for window in windows
                ],
                "description": (
                    "Maps compliance KPIs to the integration & security review cadence "
                    "so Aura can confirm evidence before each gate."
                ),
            },
        ],
        "layout": [
            _build_widget_layout("audit-trail-coverage", x=0, y=0, w=6, h=4),
            _build_widget_layout("policy-drift-trend", x=6, y=0, w=6, h=4),
            _build_widget_layout("review-readiness", x=0, y=4, w=12, h=3),
        ],
    }
    return slice_payload


def export_migration_dashboard(path: Path | str | None = None, *, indent: int = 2) -> Path:
    """Write the Grafana dashboard definition to ``path`` and return it."""

    target = Path(path) if path is not None else _DEFAULT_DASHBOARD_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    dashboard = build_migration_dashboard()
    target.write_text(json.dumps(dashboard, indent=indent, sort_keys=True), encoding="utf-8")
    return target


def export_lux_compliance_slice(path: Path | str | None = None, *, indent: int = 2) -> Path:
    """Write the LUX compliance slice definition to ``path`` and return it."""

    target = Path(path) if path is not None else _DEFAULT_LUX_SLICE_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = build_lux_compliance_slice()
    target.write_text(json.dumps(payload, indent=indent, sort_keys=True), encoding="utf-8")
    return target


def load_migration_dashboard(path: Path | str | None = None) -> dict[str, Any]:
    """Load the Grafana dashboard JSON payload from disk."""

    source = Path(path) if path is not None else _DEFAULT_DASHBOARD_PATH
    data = json.loads(source.read_text(encoding="utf-8"))
    return data


def load_lux_compliance_slice(path: Path | str | None = None) -> dict[str, Any]:
    """Load the LUX compliance slice JSON payload from disk."""

    source = Path(path) if path is not None else _DEFAULT_LUX_SLICE_PATH
    data = json.loads(source.read_text(encoding="utf-8"))
    return data


__all__ = [
    "build_migration_dashboard",
    "build_lux_compliance_slice",
    "export_migration_dashboard",
    "export_lux_compliance_slice",
    "load_migration_dashboard",
    "load_lux_compliance_slice",
]
