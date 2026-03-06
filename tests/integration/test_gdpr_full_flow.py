"""Integration test: full GDPR flow — upload → search → delete → verify gone."""

from qdrant_client import QdrantClient

from rag_engine.core.hybrid_retriever import HybridRetriever
from rag_engine.models.search import SearchType
from rag_engine.services.gdpr import GDPRService
from rag_engine.storage.bm25_store import BM25Store
from rag_engine.storage.knowledge_graph import KnowledgeGraphStore
from rag_engine.storage.qdrant_store import QdrantStore

VECTOR_SIZE = 4


def _embedding(seed: float) -> list[float]:
    return [seed, seed + 0.1, seed + 0.2, seed + 0.3]


class TestGDPRFullFlow:
    """End-to-end GDPR compliance: data must be completely removed after deletion."""

    def _setup(self):
        bm25 = BM25Store()
        graph = KnowledgeGraphStore()
        qdrant = QdrantStore(client=QdrantClient(":memory:"))
        retriever = HybridRetriever(bm25, graph)
        gdpr = GDPRService(bm25, graph, qdrant)
        return bm25, graph, qdrant, retriever, gdpr

    def test_upload_search_delete_verify(self) -> None:
        """Ingest data, find it via search, delete it, confirm it's gone."""
        bm25, graph, qdrant, retriever, gdpr = self._setup()

        # 1. Ingest
        chunks = [("doc-1", 0, "Sensitive personal data for GDPR test")]
        bm25.add_documents("gdpr-tenant", "en", chunks)
        graph.add_documents("gdpr-tenant", chunks)
        qdrant.ensure_collection("gdpr-tenant", VECTOR_SIZE)
        qdrant.add_documents("gdpr-tenant", [("doc-1", 0, chunks[0][2], _embedding(0.1))])

        # 2. Search — should find the document
        results = retriever.search(
            "gdpr-tenant",
            "Sensitive personal data",
            language="en",
            search_type=SearchType.BM25,
        )
        assert len(results) >= 1

        # 3. Delete the document
        result = gdpr.delete_document("gdpr-tenant", "doc-1", reason="GDPR erasure test")
        assert result["bm25_chunks_removed"] >= 1
        assert result["vector_chunks_removed"] >= 1

        # 4. Verify — search must return nothing
        results = retriever.search(
            "gdpr-tenant",
            "Sensitive personal data",
            language="en",
            search_type=SearchType.BM25,
        )
        assert len(results) == 0

        # Verify vector store is also empty
        assert qdrant.search("gdpr-tenant", _embedding(0.1)) == []

    def test_tenant_erasure_removes_all_documents(self) -> None:
        """Ingest multiple docs for a tenant, erase tenant, verify all gone."""
        bm25, graph, qdrant, retriever, gdpr = self._setup()

        for i in range(3):
            doc_id = f"doc-{i}"
            text = f"Document number {i} content for tenant erasure"
            bm25.add_documents("erasure-tenant", "en", [(doc_id, 0, text)])
            graph.add_documents("erasure-tenant", [(doc_id, 0, text)])

        qdrant.ensure_collection("erasure-tenant", VECTOR_SIZE)
        for i in range(3):
            qdrant.add_documents(
                "erasure-tenant",
                [(f"doc-{i}", 0, f"vec content {i}", _embedding(0.1 * (i + 1)))],
            )

        # Verify docs are searchable
        results = retriever.search(
            "erasure-tenant",
            "Document number",
            language="en",
            search_type=SearchType.BM25,
        )
        assert len(results) >= 1

        # Erase entire tenant
        result = gdpr.delete_tenant_data("erasure-tenant", reason="full tenant erasure test")
        assert result["total_removed"] >= 3

        # Verify nothing remains
        results = retriever.search(
            "erasure-tenant",
            "Document number",
            language="en",
            search_type=SearchType.BM25,
        )
        assert len(results) == 0
        assert qdrant.search("erasure-tenant", _embedding(0.1)) == []
