"""Explainability logging utilities for Meta-Agent Nova."""

from __future__ import annotations

import json
import logging
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, MutableMapping, Protocol

try:  # pragma: no cover - optional dependency
    from prometheus_client import Counter
except Exception:  # pragma: no cover - used when prometheus is unavailable
    class Counter:  # type: ignore[override]
        """Fallback implementation that mimics :class:`prometheus_client.Counter`."""

        def __init__(self, name: str, documentation: str) -> None:
            self._name = name
            self._documentation = documentation
            self._value = 0.0

        def inc(self, amount: float = 1.0) -> None:
            self._value += amount

        def count(self) -> float:
            return self._value


LOGGER = logging.getLogger("nova.explainability")


class MemoryClientProtocol(Protocol):
    """Protocol describing the client used to interface with Sophia's memory."""

    def store_decision(self, payload: Dict[str, Any]) -> None:
        """Persist a decision payload in the shared memory service."""


@dataclass(slots=True)
class ExplainabilityRecord:
    """Represents a single explainability entry."""

    timestamp: float
    category: str
    reason: str
    evidence: Dict[str, Any]
    impact: str
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "category": self.category,
            "reason": self.reason,
            "evidence": dict(self.evidence),
            "impact": self.impact,
            "metadata": dict(self.metadata),
        }


class ExplainabilityLogger:
    """Captures decision traces and forwards them to Sophia's shared memory."""

    counter: Counter = Counter(
        "decisions_logged_total",
        "Number of explainability decisions captured by Nova.",
    )

    def __init__(
        self,
        *,
        log_dir: str | Path | None = None,
        memory_client: MemoryClientProtocol | None = None,
    ) -> None:
        self._lock = threading.RLock()
        self._records: List[ExplainabilityRecord] = []
        self._memory_client = memory_client
        base_dir = Path(log_dir) if log_dir is not None else Path(__file__).resolve().parent
        self.log_dir = base_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._log_path = self.log_dir / "explain.log"
        self._json_path = self.log_dir / "explain.json"

    # ------------------------------------------------------------------
    # Properties & helpers
    # ------------------------------------------------------------------
    @property
    def records(self) -> List[ExplainabilityRecord]:
        """Return a copy of the collected records."""

        with self._lock:
            return list(self._records)

    def attach_memory_client(self, client: MemoryClientProtocol | None) -> None:
        """Assign or replace the memory client used for persisting records."""

        with self._lock:
            self._memory_client = client

    # ------------------------------------------------------------------
    # Logging API
    # ------------------------------------------------------------------
    def log_decision(
        self,
        category: str,
        *,
        reason: str,
        evidence: MutableMapping[str, Any] | Iterable[tuple[str, Any]] | None = None,
        impact: str = "",
        metadata: MutableMapping[str, Any] | None = None,
    ) -> ExplainabilityRecord:
        """Record a decision and forward it to memory if configured."""

        evidence_dict = self._to_dict(evidence)
        metadata_dict = self._to_dict(metadata)
        record = ExplainabilityRecord(
            timestamp=time.time(),
            category=category,
            reason=reason,
            evidence=evidence_dict,
            impact=impact,
            metadata=metadata_dict,
        )
        with self._lock:
            self._records.append(record)
            self._write_text_record(record)
            self._write_json_record(record)
        self.counter.inc()
        LOGGER.debug("Explainability record created: %s", record.to_dict())
        self._send_to_memory(record)
        return record

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------
    def _write_text_record(self, record: ExplainabilityRecord) -> None:
        line = (
            f"[{time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(record.timestamp))}] "
            f"{record.category}: {record.reason} | impact={record.impact}\n"
        )
        with self._log_path.open("a", encoding="utf-8") as handle:
            handle.write(line)

    def _write_json_record(self, record: ExplainabilityRecord) -> None:
        with self._json_path.open("a", encoding="utf-8") as handle:
            json.dump(record.to_dict(), handle)
            handle.write("\n")

    def _send_to_memory(self, record: ExplainabilityRecord) -> None:
        client = self._memory_client
        if client is None:
            return
        try:
            client.store_decision(record.to_dict())
        except Exception as exc:  # pragma: no cover - safety fallback
            LOGGER.warning("Failed to persist explainability record: %s", exc)

    @staticmethod
    def _to_dict(
        value: MutableMapping[str, Any] | Iterable[tuple[str, Any]] | None,
    ) -> Dict[str, Any]:
        if value is None:
            return {}
        if isinstance(value, dict):
            return dict(value)
        return {key: val for key, val in value}


__all__ = ["ExplainabilityLogger", "ExplainabilityRecord", "MemoryClientProtocol"]
