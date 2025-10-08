import json

import pytest

from nova.logging.kpi import KPITracker
from nova.monitoring.benchmarks import run_spark_baseline


@pytest.fixture
def tracker():
    return KPITracker(namespace="test")


def test_run_spark_baseline_records_checks_and_writes(tmp_path, monkeypatch, tracker):
    cpu_info = {"architecture": "x86_64", "logical_cores": 16, "processor": "Test"}
    gpu_info = {"available": True, "details": ["GPU 0", "GPU 1"]}
    network_info = {"online": True, "details": "loopback ok"}

    monkeypatch.setattr("nova.monitoring.benchmarks.check_cpu", lambda: cpu_info)
    monkeypatch.setattr("nova.monitoring.benchmarks.check_gpu", lambda: gpu_info)
    monkeypatch.setattr("nova.monitoring.benchmarks.check_network", lambda: network_info)

    snapshot = run_spark_baseline(output_dir=tmp_path, tracker=tracker)

    assert snapshot.cpu == cpu_info
    assert snapshot.gpu == gpu_info
    assert snapshot.network == network_info

    artefacts = list(tmp_path.glob("spark_baseline_*.json"))
    assert len(artefacts) == 1

    with artefacts[0].open(encoding="utf-8") as handle:
        data = json.load(handle)

    assert data["cpu"] == cpu_info
    assert data["gpu"] == gpu_info
    assert data["network"] == network_info

    metrics = tracker.snapshot()["metrics"]
    assert metrics["cpu.logical_cores"]["mean"] == pytest.approx(16.0)
    assert metrics["gpu.available"]["mean"] == pytest.approx(1.0)
    assert metrics["network.online"]["mean"] == pytest.approx(1.0)
    assert metrics["gpu.devices"]["mean"] == pytest.approx(2.0)


def test_run_spark_baseline_handles_missing_metrics(tmp_path, monkeypatch):
    cpu_info = {"architecture": "arm64", "processor": "Test"}
    gpu_info = {"available": False, "details": "nvidia-smi executable not found"}
    network_info = {"online": False, "details": "network error"}

    monkeypatch.setattr("nova.monitoring.benchmarks.check_cpu", lambda: cpu_info)
    monkeypatch.setattr("nova.monitoring.benchmarks.check_gpu", lambda: gpu_info)
    monkeypatch.setattr("nova.monitoring.benchmarks.check_network", lambda: network_info)

    snapshot = run_spark_baseline(output_dir=tmp_path)

    assert snapshot.cpu == cpu_info
    assert snapshot.gpu == gpu_info
    assert snapshot.network == network_info

    artefacts = list(tmp_path.glob("spark_baseline_*.json"))
    assert len(artefacts) == 1
