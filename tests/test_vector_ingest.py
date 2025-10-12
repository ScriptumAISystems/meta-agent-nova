from pathlib import Path

import pytest

from nova.data.vector_store import VectorStoreConfig
from nova.task_queue.vector_ingest import (
    HashingEmbedder,
    IngestSummary,
    VectorIngestConfig,
    VectorIngestor,
)


def _write_file(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def test_hashing_embedder_produces_normalised_vectors():
    embedder = HashingEmbedder(dimension=8)
    vector = embedder.embed("Nova test embedding")

    assert pytest.approx(sum(component * component for component in vector), rel=1e-5) == 1.0
    assert len(vector) == 8


def test_vector_ingestor_ingests_documents(tmp_path: Path):
    docs = tmp_path / "docs"
    docs.mkdir()
    _write_file(docs / "alpha.md", "Alpha content " * 40)
    _write_file(docs / "beta.txt", "Beta block" * 60)

    config = VectorIngestConfig(
        source_path=docs,
        store_name="test-ingest",
        dimension=16,
        chunk_size=80,
        chunk_overlap=20,
    )
    # ensure metadata schema can be customised
    config.metadata_schema = {"owner": "Team Chronos"}

    ingestor = VectorIngestor(config)
    summary = ingestor.ingest()

    assert isinstance(summary, IngestSummary)
    assert summary.total_documents == 2
    assert summary.total_chunks >= 2
    assert summary.store_description["provider"] == "in-memory"
    assert summary.sample_metadata is not None
    assert "file_name" in summary.sample_metadata

    query_vector = ingestor.embedder.embed("Alpha")
    results = ingestor.store.query(query_vector, top_k=1)
    assert results
    assert results[0].record.metadata["embedding_model"] == config.embedding_model


def test_vector_ingest_config_builds_store_config(tmp_path: Path):
    file_path = tmp_path / "note.md"
    _write_file(file_path, "Sample content")

    config = VectorIngestConfig(source_path=file_path, dimension=12)
    store_config = config.build_store_config()

    assert isinstance(store_config, VectorStoreConfig)
    assert store_config.name == "sophia-ingest"
    assert store_config.dimension == 12
    assert "source_path" in store_config.metadata_schema
