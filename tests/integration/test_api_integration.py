"""Integration tests exercising full API and storage flows."""

from fastapi.testclient import TestClient
from qdrant_client import QdrantClient

from rag_engine.api.app import create_app
from rag_engine.core.evaluation import evaluate_retrieval
from rag_engine.core.hybrid_retriever import HybridRetriever
from rag_engine.models.search import SearchType
from rag_engine.services.gdpr import GDPRService
from rag_engine.storage.bm25_store import BM25Store
from rag_engine.storage.knowledge_graph import KnowledgeGraphStore
from rag_engine.storage.qdrant_store import QdrantStore

VECTOR_SIZE = 4


def _embedding(seed: float) -> list[float]:
    """Deterministic test embedding."""
    return [seed, seed + 0.1, seed + 0.2, seed + 0.3]


class TestFullRetrievalPipeline:
    """Integration test: ingest → hybrid search → evaluate quality."""

    def _setup_stores(self):
        bm25 = BM25Store()
        graph = KnowledgeGraphStore()
        qdrant = QdrantStore(client=QdrantClient(":memory:"))
        return bm25, graph, qdrant

    def test_hybrid_search_across_all_backends(self) -> None:
        bm25, graph, qdrant = self._setup_stores()

        # Ingest same chunks into all three stores
        chunks = [
            ("doc-1", 0, "Machine Learning is transforming healthcare industry."),
            ("doc-1", 1, "Deep Learning models require large datasets for training."),
            ("doc-2", 0, "Natural Language Processing enables text understanding."),
            ("doc-2", 1, "Computer Vision algorithms detect objects in images."),
        ]

        bm25.add_documents("tenant-1", "en", chunks)
        graph.add_documents("tenant-1", chunks)

        qdrant.ensure_collection("tenant-1", VECTOR_SIZE)
        qdrant_chunks = [
            (doc_id, idx, text, _embedding(0.1 * (i + 1)))
            for i, (doc_id, idx, text) in enumerate(chunks)
        ]
        qdrant.add_documents("tenant-1", qdrant_chunks)

        retriever = HybridRetriever(bm25, graph)

        # BM25 search
        bm25_results = retriever.search(
            "tenant-1",
            "Machine Learning",
            language="en",
            search_type=SearchType.BM25,
            top_k=4,
        )
        assert len(bm25_results) > 0

        # Graph search
        graph_results = retriever.search(
            "tenant-1",
            "Machine Learning",
            language="en",
            search_type=SearchType.GRAPH,
            top_k=4,
        )
        assert len(graph_results) > 0

        # Vector search (pass results externally)
        vector_raw = qdrant.search("tenant-1", _embedding(0.1), top_k=4)
        hybrid_results = retriever.search(
            "tenant-1",
            "Machine Learning",
            language="en",
            search_type=SearchType.HYBRID,
            vector_results=vector_raw,
            top_k=4,
        )
        assert len(hybrid_results) > 0

    def test_retrieval_quality_metrics(self) -> None:
        """Evaluate retrieval quality with known ground truth."""
        bm25, graph, _ = self._setup_stores()

        bm25.add_documents(
            "tenant-1",
            "en",
            [
                ("doc-1", 0, "Python programming language"),
                ("doc-2", 0, "Java programming language"),
                ("doc-3", 0, "Cooking recipes for dinner"),
            ],
        )

        retriever = HybridRetriever(bm25, graph)
        results = retriever.search(
            "tenant-1",
            "programming language",
            language="en",
            search_type=SearchType.BM25,
            top_k=3,
        )

        retrieved_ids = [r.document_id for r in results]
        relevant_ids = {"doc-1", "doc-2"}

        metrics = evaluate_retrieval(retrieved_ids, relevant_ids)
        # Programming query should find doc-1 and doc-2
        assert metrics["context_recall"] >= 0.5
        assert metrics["mrr"] == 1.0  # first result should be relevant

    def test_multilingual_bm25_isolation(self) -> None:
        """Verify per-language isolation in BM25 search."""
        bm25, graph, _ = self._setup_stores()

        bm25.add_documents("tenant-1", "en", [("doc-1", 0, "hello world")])
        bm25.add_documents("tenant-1", "it", [("doc-2", 0, "ciao mondo")])
        bm25.add_documents("tenant-1", "ru", [("doc-3", 0, "привет мир")])

        retriever = HybridRetriever(bm25, graph)

        en_results = retriever.search(
            "tenant-1",
            "hello",
            language="en",
            search_type=SearchType.BM25,
        )
        it_results = retriever.search(
            "tenant-1",
            "ciao",
            language="it",
            search_type=SearchType.BM25,
        )

        assert len(en_results) == 1
        assert en_results[0].document_id == "doc-1"
        assert len(it_results) == 1
        assert it_results[0].document_id == "doc-2"


class TestGDPRCascadeDeletion:
    """Integration test: GDPR deletion cascades across all backends."""

    def test_delete_document_from_all_stores(self) -> None:
        bm25 = BM25Store()
        graph = KnowledgeGraphStore()
        qdrant = QdrantStore(client=QdrantClient(":memory:"))

        # Ingest into all stores
        bm25.add_documents("tenant-1", "en", [("doc-1", 0, "test data")])
        graph.add_documents("tenant-1", [("doc-1", 0, "Alice works at Acme Corp.")])
        qdrant.ensure_collection("tenant-1", VECTOR_SIZE)
        qdrant.add_documents("tenant-1", [("doc-1", 0, "test", _embedding(0.1))])

        service = GDPRService(bm25, graph, qdrant)
        result = service.delete_document("tenant-1", "doc-1")

        assert result["bm25_chunks_removed"] == 1
        assert result["graph_chunks_removed"] == 1
        assert result["vector_chunks_removed"] == 1

        # Verify empty
        assert bm25.search("tenant-1", "test", "en") == []
        assert graph.search("tenant-1", "Alice") == []
        assert qdrant.search("tenant-1", _embedding(0.1)) == []

    def test_delete_tenant_from_all_stores(self) -> None:
        bm25 = BM25Store()
        graph = KnowledgeGraphStore()
        qdrant = QdrantStore(client=QdrantClient(":memory:"))

        bm25.add_documents("tenant-1", "en", [("doc-1", 0, "data")])
        graph.add_documents("tenant-1", [("doc-1", 0, "Alice at Google.")])
        qdrant.ensure_collection("tenant-1", VECTOR_SIZE)
        qdrant.add_documents("tenant-1", [("doc-1", 0, "vec", _embedding(0.1))])

        service = GDPRService(bm25, graph, qdrant)
        service.delete_tenant_data("tenant-1")

        assert bm25.search("tenant-1", "data", "en") == []
        assert graph.search("tenant-1", "Alice") == []
        assert qdrant.search("tenant-1", _embedding(0.1)) == []

    def test_tenant_deletion_preserves_other_tenants(self) -> None:
        bm25 = BM25Store()
        graph = KnowledgeGraphStore()
        qdrant = QdrantStore(client=QdrantClient(":memory:"))

        bm25.add_documents("tenant-1", "en", [("doc-1", 0, "one")])
        bm25.add_documents("tenant-2", "en", [("doc-2", 0, "two")])
        qdrant.ensure_collection("tenant-1", VECTOR_SIZE)
        qdrant.ensure_collection("tenant-2", VECTOR_SIZE)
        qdrant.add_documents("tenant-1", [("doc-1", 0, "one", _embedding(0.1))])
        qdrant.add_documents("tenant-2", [("doc-2", 0, "two", _embedding(0.5))])

        service = GDPRService(bm25, graph, qdrant)
        service.delete_tenant_data("tenant-1")

        assert bm25.search("tenant-1", "one", "en") == []
        assert len(bm25.search("tenant-2", "two", "en")) == 1
        assert qdrant.search("tenant-1", _embedding(0.1)) == []
        assert len(qdrant.search("tenant-2", _embedding(0.5))) == 1


class TestAPIEndpoints:
    """Integration tests for HTTP API endpoints."""

    def _get_client(self) -> TestClient:
        return TestClient(create_app())

    def test_health_endpoint(self) -> None:
        client = self._get_client()
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_delete_document_returns_correct_shape(self) -> None:
        client = self._get_client()
        response = client.delete(
            "/api/v1/documents/doc-99",
            params={"tenant_id": "tenant-1", "reason": "integration test"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == "doc-99"
        assert data["tenant_id"] == "tenant-1"
        assert "bm25_chunks_removed" in data
        assert "graph_chunks_removed" in data

    def test_delete_tenant_returns_correct_shape(self) -> None:
        client = self._get_client()
        response = client.delete(
            "/api/v1/tenants/tenant-1/data",
            params={"reason": "integration test"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["tenant_id"] == "tenant-1"
        assert "message" in data

    def test_nonexistent_route_returns_404(self) -> None:
        client = self._get_client()
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404
