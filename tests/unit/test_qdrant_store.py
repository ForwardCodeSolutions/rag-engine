"""Tests for Qdrant vector store using in-memory client."""

from qdrant_client import QdrantClient

from rag_engine.storage.qdrant_store import QdrantStore

VECTOR_SIZE = 4


def _make_store() -> QdrantStore:
    """Create a QdrantStore with an in-memory Qdrant client."""
    client = QdrantClient(":memory:")
    return QdrantStore(client=client)


def _embedding(seed: float) -> list[float]:
    """Create a simple deterministic embedding for testing."""
    return [seed, seed + 0.1, seed + 0.2, seed + 0.3]


class TestQdrantStoreCollections:
    """Tests for collection management."""

    def test_ensure_collection_creates_new(self) -> None:
        store = _make_store()
        store.ensure_collection("tenant-1", VECTOR_SIZE)

        collections = [c.name for c in store._client.get_collections().collections]
        assert "tenant_tenant-1" in collections

    def test_ensure_collection_idempotent(self) -> None:
        store = _make_store()
        store.ensure_collection("tenant-1", VECTOR_SIZE)
        store.ensure_collection("tenant-1", VECTOR_SIZE)

        collections = [c.name for c in store._client.get_collections().collections]
        assert collections.count("tenant_tenant-1") == 1

    def test_separate_collections_per_tenant(self) -> None:
        store = _make_store()
        store.ensure_collection("tenant-1", VECTOR_SIZE)
        store.ensure_collection("tenant-2", VECTOR_SIZE)

        collections = [c.name for c in store._client.get_collections().collections]
        assert "tenant_tenant-1" in collections
        assert "tenant_tenant-2" in collections


class TestQdrantStoreAddAndSearch:
    """Tests for adding documents and searching."""

    def test_add_documents(self) -> None:
        store = _make_store()
        store.ensure_collection("tenant-1", VECTOR_SIZE)

        count = store.add_documents(
            "tenant-1",
            [("doc-1", 0, "hello world", _embedding(0.1))],
        )
        assert count == 1

    def test_add_empty_list(self) -> None:
        store = _make_store()
        store.ensure_collection("tenant-1", VECTOR_SIZE)
        assert store.add_documents("tenant-1", []) == 0

    def test_search_returns_results(self) -> None:
        store = _make_store()
        store.ensure_collection("tenant-1", VECTOR_SIZE)

        store.add_documents(
            "tenant-1",
            [
                ("doc-1", 0, "first chunk", _embedding(0.1)),
                ("doc-1", 1, "second chunk", _embedding(0.5)),
            ],
        )

        results = store.search("tenant-1", _embedding(0.5), top_k=2)
        assert len(results) == 2
        # Most similar should be first
        assert results[0][2] == "second chunk"
        assert results[0][3] > 0  # score > 0

    def test_search_respects_top_k(self) -> None:
        store = _make_store()
        store.ensure_collection("tenant-1", VECTOR_SIZE)

        store.add_documents(
            "tenant-1",
            [
                ("doc-1", 0, "chunk a", _embedding(0.1)),
                ("doc-1", 1, "chunk b", _embedding(0.2)),
                ("doc-1", 2, "chunk c", _embedding(0.3)),
            ],
        )

        results = store.search("tenant-1", _embedding(0.2), top_k=1)
        assert len(results) == 1

    def test_search_nonexistent_collection(self) -> None:
        store = _make_store()
        results = store.search("no-tenant", _embedding(0.1))
        assert results == []

    def test_search_result_payload(self) -> None:
        store = _make_store()
        store.ensure_collection("tenant-1", VECTOR_SIZE)

        store.add_documents(
            "tenant-1",
            [("doc-42", 3, "payload test", _embedding(0.1))],
        )

        results = store.search("tenant-1", _embedding(0.1), top_k=1)
        assert len(results) == 1
        doc_id, chunk_idx, text, score = results[0]
        assert doc_id == "doc-42"
        assert chunk_idx == 3
        assert text == "payload test"
        assert score > 0

    def test_tenant_isolation(self) -> None:
        store = _make_store()
        store.ensure_collection("tenant-1", VECTOR_SIZE)
        store.ensure_collection("tenant-2", VECTOR_SIZE)

        store.add_documents("tenant-1", [("doc-1", 0, "tenant one", _embedding(0.1))])
        store.add_documents("tenant-2", [("doc-2", 0, "tenant two", _embedding(0.2))])

        results_1 = store.search("tenant-1", _embedding(0.1), top_k=10)
        results_2 = store.search("tenant-2", _embedding(0.2), top_k=10)

        assert len(results_1) == 1
        assert results_1[0][0] == "doc-1"
        assert len(results_2) == 1
        assert results_2[0][0] == "doc-2"


class TestQdrantStoreRemoval:
    """Tests for document and tenant removal."""

    def test_remove_document(self) -> None:
        store = _make_store()
        store.ensure_collection("tenant-1", VECTOR_SIZE)

        store.add_documents(
            "tenant-1",
            [
                ("doc-1", 0, "first", _embedding(0.1)),
                ("doc-2", 0, "second", _embedding(0.5)),
            ],
        )

        removed = store.remove_document("tenant-1", "doc-1")
        assert removed == 1

        results = store.search("tenant-1", _embedding(0.1), top_k=10)
        assert len(results) == 1
        assert results[0][0] == "doc-2"

    def test_remove_nonexistent_document(self) -> None:
        store = _make_store()
        store.ensure_collection("tenant-1", VECTOR_SIZE)
        removed = store.remove_document("tenant-1", "no-such-doc")
        assert removed == 0

    def test_remove_from_nonexistent_collection(self) -> None:
        store = _make_store()
        removed = store.remove_document("no-tenant", "doc-1")
        assert removed == 0

    def test_clear_tenant(self) -> None:
        store = _make_store()
        store.ensure_collection("tenant-1", VECTOR_SIZE)

        store.add_documents("tenant-1", [("doc-1", 0, "data", _embedding(0.1))])
        store.clear_tenant("tenant-1")

        results = store.search("tenant-1", _embedding(0.1))
        assert results == []

    def test_clear_tenant_preserves_others(self) -> None:
        store = _make_store()
        store.ensure_collection("tenant-1", VECTOR_SIZE)
        store.ensure_collection("tenant-2", VECTOR_SIZE)

        store.add_documents("tenant-1", [("doc-1", 0, "one", _embedding(0.1))])
        store.add_documents("tenant-2", [("doc-2", 0, "two", _embedding(0.2))])

        store.clear_tenant("tenant-1")

        assert store.search("tenant-1", _embedding(0.1)) == []
        assert len(store.search("tenant-2", _embedding(0.2))) == 1

    def test_clear_nonexistent_tenant(self) -> None:
        store = _make_store()
        store.clear_tenant("no-such-tenant")  # should not raise

    def test_clear_all(self) -> None:
        store = _make_store()
        store.ensure_collection("tenant-1", VECTOR_SIZE)
        store.ensure_collection("tenant-2", VECTOR_SIZE)

        store.add_documents("tenant-1", [("doc-1", 0, "one", _embedding(0.1))])
        store.add_documents("tenant-2", [("doc-2", 0, "two", _embedding(0.2))])

        store.clear()

        collections = [c.name for c in store._client.get_collections().collections]
        assert collections == []

    def test_remove_multi_chunk_document(self) -> None:
        store = _make_store()
        store.ensure_collection("tenant-1", VECTOR_SIZE)

        store.add_documents(
            "tenant-1",
            [
                ("doc-1", 0, "chunk 0", _embedding(0.1)),
                ("doc-1", 1, "chunk 1", _embedding(0.2)),
                ("doc-1", 2, "chunk 2", _embedding(0.3)),
                ("doc-2", 0, "other", _embedding(0.9)),
            ],
        )

        removed = store.remove_document("tenant-1", "doc-1")
        assert removed == 3

        results = store.search("tenant-1", _embedding(0.9), top_k=10)
        assert len(results) == 1
        assert results[0][0] == "doc-2"
