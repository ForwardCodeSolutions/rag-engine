"""Integration tests verifying hybrid retrieval produces better scores than pure vector."""

from qdrant_client import QdrantClient

from rag_engine.core.hybrid_retriever import HybridRetriever
from rag_engine.models.search import SearchType
from rag_engine.storage.bm25_store import BM25Store
from rag_engine.storage.knowledge_graph import KnowledgeGraphStore
from rag_engine.storage.qdrant_store import QdrantStore

VECTOR_SIZE = 4


def _embedding(seed: float) -> list[float]:
    return [seed, seed + 0.1, seed + 0.2, seed + 0.3]


def _setup():
    bm25 = BM25Store()
    graph = KnowledgeGraphStore()
    qdrant = QdrantStore(client=QdrantClient(":memory:"))
    return bm25, graph, qdrant


class TestHybridRetrievalQuality:
    """Verify that hybrid search scores higher than individual methods."""

    def _ingest(self, bm25, graph, qdrant, tenant="t1"):
        chunks = [
            ("doc-1", 0, "Machine Learning transforms modern healthcare systems."),
            ("doc-1", 1, "Deep Learning requires large training datasets and GPUs."),
            ("doc-2", 0, "Natural Language Processing powers chatbots and search."),
            ("doc-2", 1, "Computer Vision detects objects in medical imaging."),
        ]

        bm25.add_documents(tenant, "en", chunks)
        graph.add_documents(tenant, chunks)
        qdrant.ensure_collection(tenant, VECTOR_SIZE)
        qdrant_chunks = [
            (doc_id, idx, text, _embedding(0.1 * (i + 1)))
            for i, (doc_id, idx, text) in enumerate(chunks)
        ]
        qdrant.add_documents(tenant, qdrant_chunks)

    def test_hybrid_score_exceeds_pure_vector(self) -> None:
        bm25, graph, qdrant = _setup()
        self._ingest(bm25, graph, qdrant)

        retriever = HybridRetriever(bm25, graph)
        query_vec = _embedding(0.1)

        vector_results = qdrant.search("t1", query_vec, top_k=4)
        hybrid = retriever.search(
            "t1", "Machine Learning", language="en",
            search_type=SearchType.HYBRID, vector_results=vector_results, top_k=4,
        )
        pure_vector = retriever.search(
            "t1", "Machine Learning", language="en",
            search_type=SearchType.VECTOR, vector_results=vector_results, top_k=4,
        )

        # Hybrid should return results (BM25 + graph contribute)
        assert len(hybrid) > 0
        # Hybrid top score should be >= pure vector top score
        # because hybrid aggregates scores from multiple sources
        hybrid_top = hybrid[0].score
        vector_top = pure_vector[0].score if pure_vector else 0.0
        assert hybrid_top >= vector_top

    def test_hybrid_returns_more_results_than_single_method(self) -> None:
        bm25, graph, qdrant = _setup()
        self._ingest(bm25, graph, qdrant)

        retriever = HybridRetriever(bm25, graph)

        bm25_only = retriever.search(
            "t1", "Machine Learning healthcare", language="en",
            search_type=SearchType.BM25, top_k=10,
        )
        graph_only = retriever.search(
            "t1", "Machine Learning healthcare", language="en",
            search_type=SearchType.GRAPH, top_k=10,
        )
        hybrid = retriever.search(
            "t1", "Machine Learning healthcare", language="en",
            search_type=SearchType.HYBRID, top_k=10,
        )

        # Hybrid should return at least as many results as either source alone
        assert len(hybrid) >= max(len(bm25_only), len(graph_only))

    def test_hybrid_deduplicates_across_sources(self) -> None:
        """Same chunk found by BM25 and graph should appear once in hybrid results."""
        bm25, graph, qdrant = _setup()
        self._ingest(bm25, graph, qdrant)

        retriever = HybridRetriever(bm25, graph)
        hybrid = retriever.search(
            "t1", "Machine Learning", language="en",
            search_type=SearchType.HYBRID, top_k=10,
        )

        doc_chunk_keys = [(r.document_id, r.chunk_text) for r in hybrid]
        assert len(doc_chunk_keys) == len(set(doc_chunk_keys)), "Duplicate chunks in results"
