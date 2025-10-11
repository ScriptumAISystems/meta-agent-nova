from pathlib import Path

from nova.monitoring.optimizer import optimize, summarize_build_times


def test_optimize_generates_report(tmp_path: Path) -> None:
    report = optimize(tmp_path)
    output = tmp_path / "reports" / "optimizer_summary.md"
    assert output.exists()
    assert report.metrics


def test_summarize_build_times_handles_values() -> None:
    stats = summarize_build_times([1.0, 2.0, 3.0])
    assert stats["count"] == 3.0
    assert stats["avg"] == 2.0
