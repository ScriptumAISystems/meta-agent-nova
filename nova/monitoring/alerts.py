"""Alerting utilities for Nova monitoring."""
from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Tuple

from .logging import logger


DEFAULT_THRESHOLDS_PATH = Path(__file__).resolve().parents[1] / "logging" / "kpi" / "thresholds.yaml"
SEVERITY_ORDER = ("critical", "warning")


@dataclass
class AlertEvent:
    """Represents a KPI threshold breach destined for PagerDuty/webhooks."""

    severity: str
    metric: str
    value: float
    threshold: float
    field: str
    channel: str = "pagerduty"

    def format_message(self, *, dry_run: bool = False) -> str:
        prefix = "[DRY RUN] " if dry_run else ""
        return (
            f"{prefix}{self.severity.upper()} threshold breached for {self.metric}"
            f" ({self.field}): observed={self.value} limit={self.threshold} -> channel={self.channel}"
        )

    def webhook_payload(self) -> Dict[str, Any]:
        """Build a PagerDuty-compatible payload stub."""

        return {
            "routing_key": self.channel,
            "event_action": "trigger",
            "payload": {
                "summary": f"{self.metric} exceeded {self.threshold}",
                "severity": self.severity,
                "source": "nova.monitoring",
                "custom_details": {
                    "metric": self.metric,
                    "observed": self.value,
                    "threshold": self.threshold,
                    "field": self.field,
                },
            },
        }


def load_thresholds(path: Path = DEFAULT_THRESHOLDS_PATH) -> Mapping[str, Any]:
    """Load KPI threshold configuration from YAML/JSON."""

    if not path.exists():
        logger.warning("Threshold definition file missing", extra={"path": str(path)})
        return {}

    document = path.read_text().strip()
    if not document:
        return {}

    spec = importlib.util.find_spec("yaml")
    if spec is not None:
        yaml = importlib.import_module("yaml")
        loaded = yaml.safe_load(document) or {}
    else:
        try:
            loaded = json.loads(document)
        except json.JSONDecodeError as error:
            raise ValueError(f"Invalid threshold file format: {error}") from error

    if not isinstance(loaded, Mapping):
        raise ValueError("Threshold document must be a mapping")
    return loaded


def _resolve_threshold(value: float, rules: Mapping[str, Any]) -> Optional[Tuple[str, float, str]]:
    channel = str(rules.get("channel", "pagerduty"))
    for severity in SEVERITY_ORDER:
        limit = rules.get(severity)
        if limit is None:
            continue
        limit_value = float(limit)
        if value >= limit_value:
            return severity, limit_value, channel
    warning = rules.get("warning")
    if warning is not None and value >= float(warning):
        return "warning", float(warning), channel
    return None


def evaluate_snapshot(snapshot: Mapping[str, Any], thresholds: Mapping[str, Any]) -> List[AlertEvent]:
    """Evaluate a KPI snapshot against the configured thresholds."""

    counters = snapshot.get("counters", {})
    metrics = snapshot.get("metrics", {})
    events: List[AlertEvent] = []

    for name, rules in thresholds.get("counters", {}).items():
        if not isinstance(rules, Mapping):
            continue
        value = counters.get(name)
        if value is None:
            continue
        result = _resolve_threshold(float(value), rules)
        if result is None:
            continue
        severity, limit, channel = result
        events.append(AlertEvent(severity, name, float(value), limit, "count", channel))

    for name, rules in thresholds.get("metrics", {}).items():
        if not isinstance(rules, Mapping):
            continue
        observed = metrics.get(name)
        if not isinstance(observed, Mapping):
            continue
        field = str(rules.get("field", "mean"))
        value = observed.get(field)
        if value is None:
            continue
        result = _resolve_threshold(float(value), rules)
        if result is None:
            continue
        severity, limit, channel = result
        events.append(AlertEvent(severity, name, float(value), limit, field, channel))

    return events


def dispatch_alert(event: AlertEvent, *, dry_run: bool = False) -> None:
    """Send a formatted alert to the configured channel (PagerDuty/webhook stub)."""

    message = event.format_message(dry_run=dry_run)
    payload = event.webhook_payload()
    if dry_run:
        logger.info(
            message,
            extra={
                "dry_run": True,
                "event": asdict(event),
                "payload": payload,
            },
        )
        logger.debug(
            "Simulated webhook payload",
            extra={"dry_run": True, "payload": payload, "event": asdict(event)},
        )
        return
    send_alert(event.severity, message)
    logger.debug("Dispatched webhook payload", extra={"payload": payload})


def run_alert_evaluation(
    *,
    snapshot: Mapping[str, Any],
    thresholds: Mapping[str, Any],
    dry_run: bool = False,
) -> List[AlertEvent]:
    """Evaluate thresholds and dispatch alerts for every breach."""

    events = evaluate_snapshot(snapshot, thresholds)
    if not events:
        logger.info("No KPI threshold breaches detected.")
        return []

    for event in events:
        dispatch_alert(event, dry_run=dry_run)
    return events


def _format_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def render_alert_report(
    events: Iterable[AlertEvent],
    *,
    dry_run: bool,
    snapshot: Mapping[str, Any] | None = None,
) -> str:
    """Render a Markdown summary for ``events`` suitable for the journal."""

    events = list(events)
    lines = [
        "# Nova Alert Evaluation",
        "",
        f"*Timestamp:* {_format_timestamp()}",
        f"*Mode:* {'dry-run' if dry_run else 'live'}",
        f"*Events:* {len(events)}",
        "",
    ]

    if not events:
        lines.append("Keine Schwellenwertverletzungen festgestellt. ✅")
        return "\n".join(lines).strip()

    lines.append("## Ausgelöste Alerts")
    lines.append("")
    for index, event in enumerate(events, start=1):
        lines.append(
            "{}. [{}] {} – Feld `{}` überschritt den Grenzwert (Wert: {}, Grenzwert: {}) -> Kanal: {}".format(
                index,
                event.severity.upper(),
                event.metric,
                event.field,
                event.value,
                event.threshold,
                event.channel,
            )
        )
    lines.append("")

    if snapshot:
        lines.append("## Snapshot-Auszug")
        lines.append("")
        counters = snapshot.get("counters", {})
        metrics = snapshot.get("metrics", {})
        if counters:
            lines.append("**Counters:**")
            for name, value in counters.items():
                lines.append(f"- {name}: {value}")
            lines.append("")
        if metrics:
            lines.append("**Metriken:**")
            for name, fields in metrics.items():
                if not isinstance(fields, Mapping):
                    continue
                field_repr = ", ".join(
                    f"{key}={value}" for key, value in sorted(fields.items()) if not isinstance(value, Mapping)
                )
                lines.append(f"- {name}: {field_repr}")
            lines.append("")

    return "\n".join(lines).strip()


def export_alert_report(
    events: Iterable[AlertEvent],
    *,
    output_path: Path,
    dry_run: bool,
    snapshot: Mapping[str, Any] | None = None,
) -> Path:
    """Write a Markdown alert report and return the resolved path."""

    output_path = output_path.expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report = render_alert_report(events, dry_run=dry_run, snapshot=snapshot)
    output_path.write_text(report, encoding="utf-8")
    logger.info("Alert evaluation exported", extra={"path": str(output_path), "dry_run": dry_run})
    return output_path


def execute_alert_workflow(
    *,
    thresholds_path: Path,
    snapshot_path: Path | None,
    dry_run: bool,
    export_path: Path | None = None,
) -> List[AlertEvent]:
    """Evaluate thresholds using files and optionally export a journal report."""

    thresholds = load_thresholds(thresholds_path)
    snapshot: Mapping[str, Any]
    if dry_run:
        snapshot = build_dry_run_snapshot(thresholds)
    else:
        snapshot = load_snapshot(snapshot_path)

    events = run_alert_evaluation(snapshot=snapshot, thresholds=thresholds, dry_run=dry_run)
    if export_path is not None:
        export_alert_report(events, output_path=export_path, dry_run=dry_run, snapshot=snapshot)
    return events


def build_dry_run_snapshot(thresholds: Mapping[str, Any]) -> Dict[str, Any]:
    """Generate a synthetic KPI snapshot that breaches configured limits."""

    counters: MutableMapping[str, float] = {}
    metrics: MutableMapping[str, Dict[str, float]] = {}

    for name, rules in thresholds.get("counters", {}).items():
        if not isinstance(rules, Mapping):
            continue
        limit = rules.get("critical") or rules.get("warning")
        baseline = float(limit) if limit is not None else 1.0
        counters[name] = baseline * 1.1

    for name, rules in thresholds.get("metrics", {}).items():
        if not isinstance(rules, Mapping):
            continue
        field = str(rules.get("field", "mean"))
        limit = rules.get("critical") or rules.get("warning")
        baseline = float(limit) if limit is not None else 1.0
        metrics[name] = {
            "count": 1,
            "mean": baseline,
            "min": baseline,
            "max": baseline,
            "p95": baseline,
        }
        metrics[name][field] = baseline * 1.1

    return {"namespace": "nova", "counters": counters, "metrics": metrics}


def load_snapshot(path: Optional[Path]) -> Mapping[str, Any]:
    """Load a KPI snapshot from a JSON or YAML file."""

    if path is None:
        raise ValueError("Snapshot path must be provided unless --dry-run is used")
    document = path.read_text().strip()
    if not document:
        return {}
    spec = importlib.util.find_spec("yaml")
    if spec is not None:
        yaml = importlib.import_module("yaml")
        loaded = yaml.safe_load(document) or {}
    else:
        loaded = json.loads(document)
    if not isinstance(loaded, Mapping):
        raise ValueError("Snapshot must be a mapping")
    return loaded


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate Nova KPI thresholds and dispatch alerts.")
    parser.add_argument(
        "--thresholds",
        type=Path,
        default=DEFAULT_THRESHOLDS_PATH,
        help="Path to the threshold definition file (YAML or JSON).",
    )
    parser.add_argument(
        "--snapshot",
        type=Path,
        help="Optional path to a KPI snapshot (JSON or YAML).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate a synthetic snapshot and log alerts without dispatching them.",
    )
    parser.add_argument(
        "--export",
        type=Path,
        metavar="PATH",
        help="Optional path to store a Markdown alert report for the orchestration journal.",
    )
    return parser


def main(argv: Optional[Iterable[str]] = None) -> None:
    parser = build_arg_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    logger.setLevel(logging.INFO)
    execute_alert_workflow(
        thresholds_path=args.thresholds,
        snapshot_path=args.snapshot,
        dry_run=args.dry_run,
        export_path=args.export,
    )


def send_alert(severity: str, message: str) -> None:
    """Send an alert with a given severity level via the monitoring logger."""

    severity_lower = severity.lower()
    if severity_lower == "critical":
        logger.critical(message)
    elif severity_lower == "warning":
        logger.warning(message)
    else:
        logger.info(message)


def notify_critical(message: str) -> None:
    """Notify about a critical issue."""

    send_alert("critical", message)


def notify_warning(message: str) -> None:
    """Notify about a warning issue."""

    send_alert("warning", message)


def notify_info(message: str) -> None:
    """Notify about an informational message."""

    send_alert("info", message)


if __name__ == "__main__":
    main()
