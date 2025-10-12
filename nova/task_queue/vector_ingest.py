"""Utility helpers for ingesting documents into Nova's vector store stubs.

The implementation focuses on providing Lumina and Chronos with a reproducible
pipeline that can be executed in development environments without GPU access.
It performs deterministic chunking, hashing-based embeddings and stores the
results via :mod:`nova.data.vector_store`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import math
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Mapping, Sequence

from nova.data.vector_store import (
    BaseVectorStore,
    VectorRecord,
    VectorStoreConfig,
    create_vector_store,
)


_DEFAULT_METADATA_SCHEMA: Dict[str, str] = {
    "source_path": "Pfad zum Ursprungsdokument",
    "file_name": "Dateiname ohne Pfad",
    "chunk_index": "Laufende Nummer innerhalb des Dokuments",
    "chunk_count": "Anzahl der Chunks pro Dokument",
    "embedding_model": "Verwendeter Embedding-Encoder",
}


def _normalise_source_path(path: Path) -> Path:
    if path.is_dir():
        return path
    return path.parent


def _iter_source_files(path: Path) -> Iterator[Path]:
    for candidate in sorted(path.rglob("*")):
        if candidate.is_file() and candidate.suffix.lower() in {".md", ".txt", ".rst"}:
            yield candidate


def _chunk_text(content: str, *, chunk_size: int, overlap: int) -> List[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0:
        raise ValueError("overlap cannot be negative")

    cleaned = content.replace("\r\n", "\n").strip()
    if not cleaned:
        return []

    chunks: List[str] = []
    start = 0
    length = len(cleaned)
    while start < length:
        end = min(length, start + chunk_size)
        chunk = cleaned[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == length:
            break
        start = max(0, end - overlap)
        if start == end:
            start += 1
    return chunks


class HashingEmbedder:
    """Deterministic hashing-based embedder used for tests and dry runs."""

    def __init__(self, dimension: int) -> None:
        if dimension <= 0:
            raise ValueError("dimension must be greater than zero")
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed(self, text: str) -> List[float]:
        if not text.strip():
            raise ValueError("Cannot embed empty text")

        values: List[float] = []
        counter = 0
        normalised = " ".join(text.split())
        while len(values) < self._dimension:
            digest = hashlib.sha256(f"{counter}:{normalised}".encode("utf-8")).digest()
            for byte in digest:
                # map byte (0..255) to [-1.0, 1.0]
                values.append((byte / 255.0) * 2.0 - 1.0)
                if len(values) == self._dimension:
                    break
            counter += 1

        norm = math.sqrt(sum(component * component for component in values))
        if norm:
            values = [component / norm for component in values]
        return values


@dataclass(slots=True)
class VectorIngestConfig:
    """Configuration payload describing the ingestion workflow."""

    source_path: Path
    store_name: str = "sophia-ingest"
    store_kind: str = "memory"
    metric: str = "cosine"
    dimension: int = 384
    chunk_size: int = 600
    chunk_overlap: int = 80
    encoding: str = "utf-8"
    metadata_schema: Mapping[str, str] = field(
        default_factory=lambda: dict(_DEFAULT_METADATA_SCHEMA)
    )
    embedding_model: str = "nova-hash-encoder"

    def build_store_config(self) -> VectorStoreConfig:
        schema = dict(_DEFAULT_METADATA_SCHEMA)
        schema.update(self.metadata_schema)
        return VectorStoreConfig(
            name=self.store_name,
            dimension=self.dimension,
            metric=self.metric,
            metadata_schema=schema,
        )


@dataclass(slots=True)
class IngestedChunk:
    """Represents a processed document chunk."""

    record: VectorRecord
    source_file: Path
    chunk_index: int
    chunk_count: int


@dataclass(slots=True)
class IngestSummary:
    """High level summary about an ingestion run."""

    total_documents: int
    total_chunks: int
    store_description: Mapping[str, object]
    sample_metadata: Mapping[str, str] | None = None

    def to_markdown(self) -> str:
        lines = ["# Vector Ingestion Summary", ""]
        lines.append(f"- Dokumente verarbeitet: {self.total_documents}")
        lines.append(f"- Chunks gespeichert: {self.total_chunks}")
        lines.append("")
        lines.append("## Vector Store")
        for key, value in self.store_description.items():
            lines.append(f"- **{key}**: {value}")
        if self.sample_metadata:
            lines.append("")
            lines.append("## Beispieldatensatz")
            for key, value in self.sample_metadata.items():
                lines.append(f"- {key}: {value}")
        return "\n".join(lines)


class VectorIngestor:
    """Controller that coordinates document ingestion into a vector store."""

    def __init__(self, config: VectorIngestConfig) -> None:
        self._config = config
        self._store: BaseVectorStore = create_vector_store(
            config.store_kind, config.build_store_config()
        )
        self._embedder = HashingEmbedder(config.dimension)

    @property
    def store(self) -> BaseVectorStore:
        return self._store

    @property
    def embedder(self) -> HashingEmbedder:
        return self._embedder

    def _load_content(self, path: Path) -> str:
        return path.read_text(encoding=self._config.encoding)

    def _create_record(
        self,
        *,
        chunk: str,
        file_path: Path,
        chunk_index: int,
        chunk_count: int,
    ) -> VectorRecord:
        base_id = hashlib.sha1(str(file_path).encode("utf-8")).hexdigest()[:10]
        record_id = f"{base_id}-{chunk_index:04d}"
        metadata = {
            "source_path": str(file_path.resolve()),
            "file_name": file_path.name,
            "chunk_index": str(chunk_index),
            "chunk_count": str(chunk_count),
            "embedding_model": self._config.embedding_model,
        }
        embedding = self._embedder.embed(chunk)
        return VectorRecord(record_id=record_id, values=embedding, metadata=metadata)

    def ingest(self) -> IngestSummary:
        source_root = _normalise_source_path(self._config.source_path)
        files = list(_iter_source_files(source_root))
        chunks: List[IngestedChunk] = []

        for file_path in files:
            content = self._load_content(file_path)
            text_chunks = _chunk_text(
                content,
                chunk_size=self._config.chunk_size,
                overlap=self._config.chunk_overlap,
            )
            chunk_count = len(text_chunks)
            for index, chunk in enumerate(text_chunks, start=1):
                record = self._create_record(
                    chunk=chunk,
                    file_path=file_path,
                    chunk_index=index,
                    chunk_count=chunk_count,
                )
                chunks.append(
                    IngestedChunk(
                        record=record,
                        source_file=file_path,
                        chunk_index=index,
                        chunk_count=chunk_count,
                    )
                )

        if chunks:
            self._store.upsert(chunk.record for chunk in chunks)

        sample_metadata = chunks[0].record.metadata if chunks else None
        summary = IngestSummary(
            total_documents=len(files),
            total_chunks=len(chunks),
            store_description=self._store.describe(),
            sample_metadata=sample_metadata,
        )
        return summary


__all__ = [
    "HashingEmbedder",
    "IngestSummary",
    "VectorIngestConfig",
    "VectorIngestor",
]

