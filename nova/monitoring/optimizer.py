"""Self-optimization utilities for Nova's monitoring stack."""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List

from .logging import log_info, log_warning


@dataclass(slots=True)
class OptimizationRecommendation:
    """Actionable recommendation derived from performance data."""

    metric: str
    message: str
    severity: str = "info"

    def to_markdown(self) -> str:
        icon = "✅" if self.severity == "info" else "⚠️"
        return f"- {icon} **{self.metric}**: {self.message}"


@dataclass(slots=True)
class OptimizationReport:
    """Structured summary of collected metrics and recommendations."""

    generated_at: datetime
    metrics: Dict[str, float]
    recommendations: List[OptimizationRecommendation] = field(default_factory=list)

    def to_markdown(self) -> str:
        lines = [
            "# Nova Optimizer Summary",
            "",
            f"* Generated: {self.generated_at.isoformat()}",
            "",
            "## Metrics",
        ]
        for key, value in sorted(self.metrics.items()):
            lines.append(f"- {key}: {value:.2f}")
        lines.append("")
        lines.append("## Recommendations")
        if not self.recommendations:
            lines.append("- ✅ No adjustments required; system operating within expected bounds.")
        else:
            lines.extend(rec.to_markdown() for rec in self.recommendations)
        lines.append("")
        return "\n".join(lines).strip() + "\n"

    def to_dict(self) -> dict[str, object]:
        return {
            "generated_at": self.generated_at.isoformat(),
            "metrics": self.metrics,
            "recommendations": [
                {"metric": rec.metric, "message": rec.message, "severity": rec.severity}
                for rec in self.recommendations
            ],
        }


def _collect_metrics(base_path: Path) -> Dict[str, float]:
    logs_dir = base_path / "logs"
    reports_dir = base_path / "reports"
    log_files = list(logs_dir.glob("*.log")) + list(logs_dir.glob("*.jsonl"))
    report_files = list(reports_dir.glob("*.md"))
    metrics = {
        "log_files": float(len(log_files)),
        "reports": float(len(report_files)),
        "artifacts": float(len(list((base_path / "artifacts").glob("**/*")))) if (base_path / "artifacts").exists() else 0.0,
    }
    return metrics


def _analyse_metrics(metrics: Dict[str, float]) -> List[OptimizationRecommendation]:
    recommendations: List[OptimizationRecommendation] = []
    log_volume = metrics.get("log_files", 0.0)
    if log_volume == 0:
        recommendations.append(
            OptimizationRecommendation(
                "log_files",
                "No log files detected. Enable monitoring handlers to capture runtime diagnostics.",
                severity="warning",
            )
        )
    report_count = metrics.get("reports", 0.0)
    if report_count < 2:
        recommendations.append(
            OptimizationRecommendation(
                "reports",
                "Generate DGX audit and optimizer reports to improve explainability coverage.",
                severity="warning",
            )
        )
    return recommendations


def optimize(base_path: Path) -> OptimizationReport:
    """Collect metrics and persist an optimizer report under ``reports/``."""

    metrics = _collect_metrics(base_path)
    recommendations = _analyse_metrics(metrics)
    report = OptimizationReport(generated_at=datetime.utcnow(), metrics=metrics, recommendations=recommendations)
    reports_dir = base_path / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    destination = reports_dir / "optimizer_summary.md"
    destination.write_text(report.to_markdown(), encoding="utf-8")
    log_info(f"Optimizer report written to {destination}")
    if recommendations:
        log_warning("Optimizer identified improvements for Nova pipelines.")
    return report


def summarize_build_times(durations: Iterable[float]) -> Dict[str, float]:
    """Helper for unit tests – derive statistics for build durations."""

    values = list(durations)
    if not values:
        return {"count": 0.0, "avg": 0.0, "p95": 0.0}
    return {
        "count": float(len(values)),
        "avg": float(sum(values) / len(values)),
        "p95": float(statistics.quantiles(values, n=100)[94] if len(values) >= 20 else max(values)),
    }


__all__ = ["OptimizationRecommendation", "OptimizationReport", "optimize", "summarize_build_times"]
