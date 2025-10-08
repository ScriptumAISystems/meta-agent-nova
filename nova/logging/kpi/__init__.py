"""KPI tracking utilities for Nova's monitoring layer."""
from __future__ import annotations

import statistics
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, MutableMapping

from ..config import get_logger


@dataclass
class MetricAggregate:
    """Aggregated statistics for a single numeric metric."""

    count: int = 0
    total: float = 0.0
    values: List[float] = field(default_factory=list)

    def observe(self, value: float) -> None:
        self.count += 1
        self.total += value
        self.values.append(value)

    @property
    def mean(self) -> float:
        return self.total / self.count if self.count else 0.0

    @property
    def maximum(self) -> float:
        return max(self.values) if self.values else 0.0

    @property
    def minimum(self) -> float:
        return min(self.values) if self.values else 0.0

    @property
    def percentile_95(self) -> float:
        if not self.values:
            return 0.0
        if len(self.values) == 1:
            return self.values[0]
        return statistics.quantiles(self.values, n=100)[94]


class KPITracker:
    """Thread-safe KPI tracker used to surface operational insights."""

    def __init__(self, *, namespace: str = "nova") -> None:
        self._namespace = namespace
        self._logger = get_logger(f"{namespace}.kpi")
        self._counters: MutableMapping[str, int] = defaultdict(int)
        self._metrics: MutableMapping[str, MetricAggregate] = defaultdict(MetricAggregate)
        self._lock = threading.Lock()

    def increment(self, name: str, amount: int = 1) -> None:
        with self._lock:
            self._counters[name] += amount
        self._logger.debug("KPI counter increment", extra={"metric": name, "value": amount})

    def observe(self, name: str, value: float) -> None:
        with self._lock:
            self._metrics[name].observe(value)
        self._logger.debug("KPI observation", extra={"metric": name, "value": value})

    def snapshot(self) -> Dict[str, object]:
        with self._lock:
            counters = dict(self._counters)
            metrics = {
                name: {
                    "count": aggregate.count,
                    "mean": aggregate.mean,
                    "min": aggregate.minimum,
                    "max": aggregate.maximum,
                    "p95": aggregate.percentile_95,
                }
                for name, aggregate in self._metrics.items()
            }
        return {"namespace": self._namespace, "counters": counters, "metrics": metrics}

    def emit(self) -> None:
        snapshot = self.snapshot()
        self._logger.info("KPI snapshot", extra=snapshot)


__all__ = ["KPITracker", "MetricAggregate"]
