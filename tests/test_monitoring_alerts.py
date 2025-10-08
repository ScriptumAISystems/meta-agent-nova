"""Tests for nova.monitoring.alerts."""

from __future__ import annotations

import json
from pathlib import Path

from nova.monitoring import alerts


def _sample_thresholds() -> dict:
    return {
        "counters": {"queue.failures": {"warning": 2, "critical": 4}},
        "metrics": {
            "queue.latency": {"field": "p95", "warning": 100, "critical": 150}
        },
    }


def test_build_dry_run_snapshot_exceeds_thresholds():
    thresholds = _sample_thresholds()
    snapshot = alerts.build_dry_run_snapshot(thresholds)

    assert snapshot["counters"]["queue.failures"] > thresholds["counters"]["queue.failures"]["critical"]
    assert (
        snapshot["metrics"]["queue.latency"]["p95"]
        > thresholds["metrics"]["queue.latency"]["critical"]
    )


def test_render_alert_report_contains_event_details():
    event = alerts.AlertEvent(
        severity="critical",
        metric="queue.latency",
        value=175.0,
        threshold=150.0,
        field="p95",
        channel="pagerduty",
    )
    snapshot = {
        "counters": {"queue.failures": 5},
        "metrics": {"queue.latency": {"p95": 175.0, "count": 10}},
    }

    report = alerts.render_alert_report([event], dry_run=True, snapshot=snapshot)

    assert "# Nova Alert Evaluation" in report
    assert "queue.latency" in report
    assert "p95" in report
    assert "Grenzwert" in report


def test_export_alert_report_writes_markdown(tmp_path: Path):
    event = alerts.AlertEvent(
        severity="warning",
        metric="queue.failures",
        value=6.0,
        threshold=2.0,
        field="count",
        channel="pagerduty",
    )
    export_path = tmp_path / "alert.md"

    result_path = alerts.export_alert_report([event], output_path=export_path, dry_run=False)

    assert result_path == export_path.resolve()
    content = export_path.read_text(encoding="utf-8")
    assert "Ausgelöste Alerts" in content
    assert "queue.failures" in content


def test_execute_alert_workflow_dry_run_exports_report(tmp_path: Path):
    thresholds_path = tmp_path / "thresholds.json"
    thresholds_path.write_text(json.dumps(_sample_thresholds()), encoding="utf-8")
    export_path = tmp_path / "journal" / "alerts.md"

    events = alerts.execute_alert_workflow(
        thresholds_path=thresholds_path,
        snapshot_path=None,
        dry_run=True,
        export_path=export_path,
    )

    assert events, "Dry-run evaluation should create synthetic breaches."
    assert export_path.exists()
    markdown = export_path.read_text(encoding="utf-8")
    assert "Nova Alert Evaluation" in markdown

