"""Baseline benchmark helpers for Spark hardware validation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Mapping

from nova.logging.kpi import KPITracker
from nova.system.checks import check_cpu, check_gpu, check_network

_DEFAULT_ARTIFACT_DIR = Path(__file__).resolve().parents[1] / "logging" / "kpi"


def _serialise_timestamp(dt: datetime) -> tuple[str, str]:
    """Return ISO timestamp and a filename safe variant."""

    iso_timestamp = dt.isoformat(timespec="seconds")
    safe_timestamp = iso_timestamp.replace(":", "-")
    return iso_timestamp, safe_timestamp


@dataclass(frozen=True)
class BaselineSnapshot:
    """Container holding the results of a baseline benchmark run."""

    timestamp: str
    cpu: Mapping[str, Any]
    gpu: Mapping[str, Any]
    network: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _store_snapshot(
    snapshot: BaselineSnapshot, output_dir: Path, safe_timestamp: str
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"spark_baseline_{safe_timestamp}.json"
    with path.open("w", encoding="utf-8") as handle:
        json.dump(snapshot.to_dict(), handle, indent=2, sort_keys=True)
    return path


def _observe_metrics(snapshot: BaselineSnapshot, tracker: KPITracker) -> None:
    cpu_logical = snapshot.cpu.get("logical_cores")
    if isinstance(cpu_logical, (int, float)):
        tracker.observe("cpu.logical_cores", float(cpu_logical))

    gpu_available = snapshot.gpu.get("available")
    tracker.observe("gpu.available", 1.0 if bool(gpu_available) else 0.0)

    gpu_details = snapshot.gpu.get("details")
    if isinstance(gpu_details, (list, tuple)):
        tracker.observe("gpu.devices", float(len(gpu_details)))

    network_online = snapshot.network.get("online")
    tracker.observe("network.online", 1.0 if bool(network_online) else 0.0)


def run_spark_baseline(
    *,
    output_dir: Path | str | None = None,
    tracker: KPITracker | None = None,
) -> BaselineSnapshot:
    """Execute CPU, GPU and network checks and persist the measurements.

    Parameters
    ----------
    output_dir:
        Optional directory used to store the generated JSON artefact. Defaults to
        ``nova/logging/kpi`` when omitted.
    tracker:
        Optional :class:`~nova.logging.kpi.KPITracker` that records numeric
        observations derived from the captured metrics.
    """

    cpu_info = check_cpu()
    gpu_info = check_gpu()
    network_info = check_network()

    timestamp, safe_timestamp = _serialise_timestamp(datetime.now(timezone.utc))
    snapshot = BaselineSnapshot(
        timestamp=timestamp,
        cpu=cpu_info,
        gpu=gpu_info,
        network=network_info,
    )

    artefact_dir = Path(output_dir) if output_dir is not None else _DEFAULT_ARTIFACT_DIR
    _store_snapshot(snapshot, artefact_dir, safe_timestamp)

    if tracker is not None:
        _observe_metrics(snapshot, tracker)

    return snapshot


__all__ = ["BaselineSnapshot", "run_spark_baseline"]

