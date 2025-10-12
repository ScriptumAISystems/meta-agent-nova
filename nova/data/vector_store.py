"""Vector database abstractions and in-memory prototypes for Lumina."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import sqrt
from typing import Dict, Iterable, List, Mapping, MutableMapping, Sequence


_SUPPORTED_METRICS = {"cosine", "dot", "euclidean"}


@dataclass(slots=True)
class VectorStoreConfig:
    """Static configuration for a vector store backend."""

    name: str
    dimension: int
    metric: str = "cosine"
    metadata_schema: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Vector store name must be provided")
        if self.dimension <= 0:
            raise ValueError("Vector dimension must be a positive integer")
        metric = self.metric.lower()
        if metric not in _SUPPORTED_METRICS:
            raise ValueError(f"Unsupported similarity metric: {self.metric}")
        self.metric = metric


@dataclass(slots=True)
class VectorRecord:
    """Container for an embedded document."""

    record_id: str
    values: Sequence[float]
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.record_id:
            raise ValueError("VectorRecord requires a non-empty record_id")
        if not self.values:
            raise ValueError("VectorRecord requires embedding values")


@dataclass(slots=True)
class VectorQueryResult:
    """Query response entry returned by a vector store."""

    record: VectorRecord
    score: float


class BaseVectorStore:
    """Abstract vector store with common validation helpers."""

    provider: str = "generic"

    def __init__(self, config: VectorStoreConfig) -> None:
        self._config = config

    @property
    def config(self) -> VectorStoreConfig:
        return self._config

    def upsert(self, records: Iterable[VectorRecord]) -> int:
        raise NotImplementedError

    def query(self, values: Sequence[float], *, top_k: int = 5) -> List[VectorQueryResult]:
        raise NotImplementedError

    def delete(self, record_ids: Iterable[str]) -> int:
        raise NotImplementedError

    def describe(self) -> Dict[str, object]:
        return {
            "name": self._config.name,
            "dimension": self._config.dimension,
            "metric": self._config.metric,
            "provider": self.provider,
        }

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------
    def _normalise_values(self, values: Sequence[float]) -> List[float]:
        if len(values) != self._config.dimension:
            raise ValueError(
                f"Expected vector of dimension {self._config.dimension}, received {len(values)}"
            )
        return [float(value) for value in values]

    def _score(self, lhs: Sequence[float], rhs: Sequence[float]) -> float:
        metric = self._config.metric
        if metric == "cosine":
            return _cosine_similarity(lhs, rhs)
        if metric == "dot":
            return float(sum(x * y for x, y in zip(lhs, rhs)))
        if metric == "euclidean":
            return -_euclidean_distance(lhs, rhs)
        raise RuntimeError(f"Metric {metric!r} is not supported")


class InMemoryVectorStore(BaseVectorStore):
    """Simple in-memory implementation for development and tests."""

    provider = "in-memory"

    def __init__(self, config: VectorStoreConfig) -> None:
        super().__init__(config)
        self._records: MutableMapping[str, VectorRecord] = {}

    def upsert(self, records: Iterable[VectorRecord]) -> int:
        count = 0
        for record in records:
            values = self._normalise_values(record.values)
            metadata = dict(record.metadata)
            stored = VectorRecord(record_id=record.record_id, values=values, metadata=metadata)
            self._records[stored.record_id] = stored
            count += 1
        return count

    def query(self, values: Sequence[float], *, top_k: int = 5) -> List[VectorQueryResult]:
        if top_k <= 0:
            raise ValueError("top_k must be greater than zero")
        query_vector = self._normalise_values(values)
        scored: List[VectorQueryResult] = []
        for record in self._records.values():
            score = self._score(query_vector, record.values)
            scored.append(VectorQueryResult(record=record, score=score))
        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:top_k]

    def delete(self, record_ids: Iterable[str]) -> int:
        removed = 0
        for record_id in record_ids:
            if record_id in self._records:
                del self._records[record_id]
                removed += 1
        return removed

    def describe(self) -> Dict[str, object]:
        base = super().describe()
        base["records"] = len(self._records)
        base["metadata_schema"] = dict(self._config.metadata_schema)
        return base


class PineconeVectorStore(InMemoryVectorStore):
    """Stubbed Pinecone backend using the in-memory implementation."""

    provider = "pinecone"

    def describe(self) -> Dict[str, object]:
        base = super().describe()
        base.update({
            "environment": "us-west1-gcp",
            "deployment": "sophia-embeddings",
        })
        return base


class FaissVectorStore(InMemoryVectorStore):
    """Stubbed FAISS backend using the in-memory implementation."""

    provider = "faiss"

    def describe(self) -> Dict[str, object]:
        base = super().describe()
        base.update({
            "index_type": "IVF4096,Flat",
            "storage": "local",
        })
        return base


def create_vector_store(kind: str, config: VectorStoreConfig) -> BaseVectorStore:
    """Factory that returns a configured vector store implementation."""

    if not kind:
        raise ValueError("Vector store kind must be provided")
    normalised = kind.strip().lower()
    if normalised == "pinecone":
        return PineconeVectorStore(config)
    if normalised == "faiss":
        return FaissVectorStore(config)
    if normalised in {"memory", "in-memory", "mock"}:
        return InMemoryVectorStore(config)
    raise ValueError(f"Unsupported vector store kind: {kind}")


def _cosine_similarity(lhs: Sequence[float], rhs: Sequence[float]) -> float:
    numerator = sum(x * y for x, y in zip(lhs, rhs))
    lhs_norm = sqrt(sum(x * x for x in lhs))
    rhs_norm = sqrt(sum(y * y for y in rhs))
    if lhs_norm == 0 or rhs_norm == 0:
        return 0.0
    return float(numerator / (lhs_norm * rhs_norm))


def _euclidean_distance(lhs: Sequence[float], rhs: Sequence[float]) -> float:
    return sqrt(sum((x - y) ** 2 for x, y in zip(lhs, rhs)))


__all__ = [
    "BaseVectorStore",
    "FaissVectorStore",
    "InMemoryVectorStore",
    "PineconeVectorStore",
    "VectorQueryResult",
    "VectorRecord",
    "VectorStoreConfig",
    "create_vector_store",
]
