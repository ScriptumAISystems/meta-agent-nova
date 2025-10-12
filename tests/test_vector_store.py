from nova.data.vector_store import (
    FaissVectorStore,
    InMemoryVectorStore,
    PineconeVectorStore,
    VectorQueryResult,
    VectorRecord,
    VectorStoreConfig,
    create_vector_store,
)


def _sample_config(metric: str = "cosine") -> VectorStoreConfig:
    return VectorStoreConfig(name="sophia", dimension=3, metric=metric, metadata_schema={"topic": "str"})


def test_in_memory_upsert_and_query() -> None:
    store = InMemoryVectorStore(_sample_config())
    inserted = store.upsert(
        [
            VectorRecord("alpha", [1.0, 0.0, 0.0], {"topic": "greeting"}),
            VectorRecord("beta", [0.0, 1.0, 0.0], {"topic": "closing"}),
        ]
    )
    assert inserted == 2

    results = store.query([1.0, 0.0, 0.0], top_k=1)
    assert len(results) == 1
    assert isinstance(results[0], VectorQueryResult)
    assert results[0].record.record_id == "alpha"
    assert results[0].score == 1.0


def test_delete_removes_vectors() -> None:
    store = InMemoryVectorStore(_sample_config())
    store.upsert([VectorRecord("item", [0.1, 0.2, 0.3])])
    removed = store.delete(["item", "missing"])
    assert removed == 1
    assert store.query([0.1, 0.2, 0.3], top_k=1) == []


def test_factory_creates_specialised_backends() -> None:
    config = _sample_config()
    pinecone = create_vector_store("pinecone", config)
    assert isinstance(pinecone, PineconeVectorStore)
    faiss = create_vector_store("faiss", config)
    assert isinstance(faiss, FaissVectorStore)
    memory = create_vector_store("mock", config)
    assert isinstance(memory, InMemoryVectorStore)


def test_query_supports_alternative_metrics() -> None:
    dot_store = InMemoryVectorStore(_sample_config(metric="dot"))
    dot_store.upsert([VectorRecord("dot", [1.0, 2.0, 3.0])])
    dot_score = dot_store.query([0.5, 1.0, 1.5], top_k=1)[0].score

    euclidean_store = InMemoryVectorStore(_sample_config(metric="euclidean"))
    euclidean_store.upsert([VectorRecord("dist", [0.0, 0.0, 0.0])])
    euclidean_score = euclidean_store.query([1.0, 0.0, 0.0], top_k=1)[0].score

    assert dot_score == 7.0
    assert euclidean_score == -1.0


def test_dimension_mismatch_raises() -> None:
    store = InMemoryVectorStore(_sample_config())
    store.upsert([VectorRecord("alpha", [1.0, 0.0, 0.0])])
    try:
        store.query([1.0, 0.0], top_k=1)
    except ValueError as exc:
        assert "Expected vector of dimension" in str(exc)
    else:  # pragma: no cover - defensive
        assert False, "Expected ValueError"


def test_describe_includes_metadata_schema() -> None:
    store = PineconeVectorStore(_sample_config())
    store.upsert([VectorRecord("alpha", [1.0, 0.0, 0.0])])
    description = store.describe()
    assert description["provider"] == "pinecone"
    assert description["metadata_schema"] == {"topic": "str"}
    assert description["records"] == 1
