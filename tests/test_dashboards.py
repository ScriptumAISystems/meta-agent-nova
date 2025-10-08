from __future__ import annotations

import json
from pathlib import Path

import pytest

from nova.monitoring import dashboards as dashboards_module
from nova.monitoring.dashboards import (
    build_migration_dashboard,
    export_migration_dashboard,
    load_migration_dashboard,
)


def _get_panel(dashboard: dict[str, object], title: str) -> dict[str, object]:
    panels = dashboard.get("panels", [])
    assert isinstance(panels, list)
    for panel in panels:
        if isinstance(panel, dict) and panel.get("title") == title:
            return panel
    raise AssertionError(f"panel '{title}' not found")


def test_build_migration_dashboard_contains_expected_panels():
    dashboard = build_migration_dashboard()
    assert dashboard["title"] == "Spark Migration KPIs"

    duration_panel = _get_panel(dashboard, "Deployment Duration Trend")
    targets = duration_panel.get("targets", [])
    assert any(
        "nova_deployment_duration_seconds" in target.get("expr", "")
        for target in targets
        if isinstance(target, dict)
    )

    burn_panel = _get_panel(dashboard, "Error Budget Burn")
    burn_targets = burn_panel.get("targets", [])
    assert any(
        "nova_error_budget_consumed" in target.get("expr", "")
        for target in burn_targets
        if isinstance(target, dict)
    )

    remaining_panel = _get_panel(dashboard, "Remaining Error Budget")
    remaining_targets = remaining_panel.get("targets", [])
    assert any(
        "nova_error_budget_remaining" in target.get("expr", "")
        for target in remaining_targets
        if isinstance(target, dict)
    )


def test_export_and_load_roundtrip(tmp_path: Path):
    target = tmp_path / "dashboard.json"
    exported = export_migration_dashboard(target)
    assert exported == target
    payload = json.loads(target.read_text())
    assert payload["uid"] == "spark-migration-kpis"

    loaded = load_migration_dashboard(target)
    assert loaded == payload


def test_export_uses_default_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    default_path = tmp_path / "spark.json"
    monkeypatch.setattr(dashboards_module, "_DEFAULT_DASHBOARD_PATH", default_path)

    exported = export_migration_dashboard()
    assert exported == default_path
    assert default_path.exists()
