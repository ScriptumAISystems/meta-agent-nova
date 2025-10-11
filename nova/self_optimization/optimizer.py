"""Self-optimisation routines for Nova."""

from __future__ import annotations

import statistics
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Sequence

from ..explainability import ExplainabilityLogger


@dataclass(slots=True)
class PipelineMetrics:
    """Collection of pipeline metrics captured for an optimisation cycle."""

    build_time_seconds: float
    error_rate: float
    coverage: float


@dataclass(slots=True)
class OptimizationReport:
    """Summary of an optimisation cycle."""

    reward: float
    recommendation: str
    metrics: List[PipelineMetrics] = field(default_factory=list)
    generated_at: float = field(default_factory=time.time)

    def to_markdown(self) -> str:
        header = ["# Optimisation Report", "", f"* Reward: {self.reward:.2f}", f"* Recommendation: {self.recommendation}"]
        if not self.metrics:
            header.append("\n_No metrics available._")
            return "\n".join(header)
        header.append("\n## Metrics")
        for metric in self.metrics:
            header.append(
                f"- build_time={metric.build_time_seconds:.2f}s, "
                f"error_rate={metric.error_rate:.3f}, coverage={metric.coverage:.3f}"
            )
        return "\n".join(header)


class PipelineOptimizer:
    """Analyses pipeline telemetry and produces optimisation guidance."""

    def __init__(
        self,
        *,
        report_path: str | Path | None = None,
        logger: ExplainabilityLogger | None = None,
    ) -> None:
        base_path = Path(report_path) if report_path else Path("reports/optimizer_report.md")
        self.report_path = base_path
        self.report_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = logger or ExplainabilityLogger()

    # ------------------------------------------------------------------
    def analyse(self, metrics: Sequence[PipelineMetrics]) -> OptimizationReport:
        """Analyse telemetry and derive an optimisation recommendation."""

        if not metrics:
            recommendation = "Collect more telemetry before optimising."
            report = OptimizationReport(reward=0.0, recommendation=recommendation, metrics=[])
            self.logger.log_decision(
                "optimizer",
                reason="Insufficient metrics for optimisation.",
                evidence={"metrics": []},
                impact="no-change",
            )
            self._write_report(report)
            return report

        avg_build = statistics.mean(metric.build_time_seconds for metric in metrics)
        avg_error = statistics.mean(metric.error_rate for metric in metrics)
        avg_coverage = statistics.mean(metric.coverage for metric in metrics)

        performance_gain = max(0.0, 1.0 - avg_build / max(metrics[0].build_time_seconds, 1e-6))
        reward = (performance_gain * 100.0) - (avg_error * 100.0)
        if avg_coverage < 0.85:
            recommendation = "Increase test coverage through targeted testing." \
                + " Focus on the weakest modules."  # noqa: E501
        elif avg_error > 0.05:
            recommendation = "Stabilise pipelines by addressing flaky tests first."
        else:
            recommendation = "Pipelines healthy. Continue incremental improvements."

        report = OptimizationReport(
            reward=reward,
            recommendation=recommendation,
            metrics=list(metrics),
        )
        self.logger.log_decision(
            "optimizer",
            reason="Completed optimisation cycle.",
            evidence={
                "avg_build_time": avg_build,
                "avg_error_rate": avg_error,
                "avg_coverage": avg_coverage,
                "reward": reward,
            },
            impact="pipeline-adjustment",
        )
        self._write_report(report)
        return report

    # ------------------------------------------------------------------
    def _write_report(self, report: OptimizationReport) -> None:
        self.report_path.write_text(report.to_markdown(), encoding="utf-8")


__all__ = ["OptimizationReport", "PipelineMetrics", "PipelineOptimizer"]
