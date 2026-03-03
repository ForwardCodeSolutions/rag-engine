"""Tests for hybrid retriever and re-ranker."""

from rag_engine.core.hybrid_retriever import HybridRetriever
from rag_engine.core.reranker import ScoredChunk, normalize_scores, rerank
from rag_engine.models.search import SearchType
from rag_engine.storage.bm25_store import BM25Store
from rag_engine.storage.knowledge_graph import KnowledgeGraphStore


class TestNormalizeScores:
    """Tests for score normalization."""

    def test_normalizes_to_zero_one(self) -> None:
        result = normalize_scores([1.0, 2.0, 3.0, 4.0, 5.0])
        assert result[0] == 0.0
        assert result[-1] == 1.0

    def test_two_values(self) -> None:
        result = normalize_scores([10.0, 20.0])
        assert result == [0.0, 1.0]

    def test_equal_values_returns_ones(self) -> None:
        result = normalize_scores([5.0, 5.0, 5.0])
        assert result == [1.0, 1.0, 1.0]

    def test_single_value_returns_one(self) -> None:
        assert normalize_scores([42.0]) == [1.0]

    def test_empty_returns_empty(self) -> None:
        assert normalize_scores([]) == []


class TestRerank:
    """Tests for weighted re-ranking."""

    def test_reranks_by_combined_score(self) -> None:
        chunks = [
            ScoredChunk("doc-1", 0, "low", vector_score=0.1, bm25_score=0.1),
            ScoredChunk("doc-2", 0, "high", vector_score=0.9, bm25_score=0.9),
        ]
        result = rerank(chunks)
        assert result[0].document_id == "doc-2"
        assert result[0].combined_score > result[1].combined_score

    def test_respects_weights(self) -> None:
        chunks = [
            ScoredChunk("doc-1", 0, "bm25 strong", bm25_score=10.0),
            ScoredChunk("doc-2", 0, "vector strong", vector_score=10.0),
        ]
        # Heavy BM25 weight should favor doc-1
        result = rerank(chunks, vector_weight=0.1, bm25_weight=0.8, graph_weight=0.1)
        assert result[0].document_id == "doc-1"

    def test_empty_input(self) -> None:
        assert rerank([]) == []

    def test_combined_scores_are_set(self) -> None:
        chunks = [ScoredChunk("doc-1", 0, "text", vector_score=1.0)]
        result = rerank(chunks)
        assert result[0].combined_score > 0


class TestHybridRetrieverBM25Only:
    """Tests for hybrid retriever using BM25 search only."""

    def _setup_store(self) -> tuple[BM25Store, KnowledgeGraphStore]:
        bm25 = BM25Store()
        bm25.add_documents(
            "tenant-1",
            "en",
            [
                ("doc-1", 0, "machine learning algorithms and neural networks"),
                ("doc-2", 0, "python programming language tutorial"),
                ("doc-3", 0, "deep learning neural networks architecture"),
            ],
        )
        graph = KnowledgeGraphStore()
        return bm25, graph

    def test_bm25_search_returns_results(self) -> None:
        bm25, graph = self._setup_store()
        retriever = HybridRetriever(bm25, graph)

        results = retriever.search("tenant-1", "neural networks", search_type=SearchType.BM25)
        assert len(results) >= 1
        assert all(r.score > 0 for r in results)

    def test_bm25_search_respects_top_k(self) -> None:
        bm25, graph = self._setup_store()
        retriever = HybridRetriever(bm25, graph)

        results = retriever.search("tenant-1", "neural", search_type=SearchType.BM25, top_k=1)
        assert len(results) <= 1


class TestHybridRetrieverGraphOnly:
    """Tests for hybrid retriever using graph search only."""

    def test_graph_search_returns_results(self) -> None:
        bm25 = BM25Store()
        graph = KnowledgeGraphStore()
        graph.add_documents(
            "tenant-1",
            [
                ("doc-1", 0, "Alice works at Acme Corporation in Berlin."),
                ("doc-2", 0, "Bob lives in Paris near the Eiffel Tower."),
            ],
        )

        retriever = HybridRetriever(bm25, graph)
        results = retriever.search("tenant-1", "Alice", search_type=SearchType.GRAPH)
        assert len(results) >= 1
        assert results[0].document_id == "doc-1"


class TestHybridRetrieverHybrid:
    """Tests for full hybrid search combining multiple sources."""

    def test_hybrid_merges_bm25_and_graph(self) -> None:
        bm25 = BM25Store()
        bm25.add_documents(
            "tenant-1",
            "en",
            [
                ("doc-1", 0, "Alice works at Acme Corporation"),
                ("doc-2", 0, "python programming tutorial"),
            ],
        )
        graph = KnowledgeGraphStore()
        graph.add_documents(
            "tenant-1",
            [
                ("doc-1", 0, "Alice works at Acme Corporation"),
                ("doc-3", 0, "Bob at Acme Corporation in Berlin"),
            ],
        )

        retriever = HybridRetriever(bm25, graph)
        results = retriever.search("tenant-1", "Acme", search_type=SearchType.HYBRID)

        doc_ids = [r.document_id for r in results]
        # doc-1 appears in both BM25 and graph, should be present
        assert "doc-1" in doc_ids

    def test_hybrid_deduplicates(self) -> None:
        bm25 = BM25Store()
        bm25.add_documents("tenant-1", "en", [("doc-1", 0, "Alice at Acme")])

        graph = KnowledgeGraphStore()
        graph.add_documents("tenant-1", [("doc-1", 0, "Alice at Acme")])

        retriever = HybridRetriever(bm25, graph)
        results = retriever.search("tenant-1", "Alice")

        # doc-1 chunk 0 should appear only once despite being in both sources
        keys = [(r.document_id, r.chunk_text) for r in results]
        assert len(keys) == len(set(keys))

    def test_hybrid_with_vector_results(self) -> None:
        bm25 = BM25Store()
        graph = KnowledgeGraphStore()
        retriever = HybridRetriever(bm25, graph)

        vector_results = [
            ("doc-1", 0, "semantic match text", 0.95),
            ("doc-2", 0, "another match", 0.80),
        ]

        results = retriever.search(
            "tenant-1",
            "query",
            vector_results=vector_results,
            search_type=SearchType.VECTOR,
        )
        assert len(results) == 2
        assert results[0].document_id == "doc-1"

    def test_hybrid_chunk_found_in_multiple_sources_scores_higher(self) -> None:
        bm25 = BM25Store()
        bm25.add_documents(
            "tenant-1",
            "en",
            [
                ("doc-1", 0, "Alice works at Acme Corporation"),
                ("doc-2", 0, "Bob works at some company"),
            ],
        )
        graph = KnowledgeGraphStore()
        graph.add_documents(
            "tenant-1",
            [("doc-1", 0, "Alice works at Acme Corporation")],
        )

        retriever = HybridRetriever(bm25, graph)
        results = retriever.search("tenant-1", "Alice Acme")

        # doc-1 is in both BM25 and graph, should rank first
        if len(results) >= 2:
            assert results[0].document_id == "doc-1"

    def test_empty_results(self) -> None:
        bm25 = BM25Store()
        graph = KnowledgeGraphStore()
        retriever = HybridRetriever(bm25, graph)

        results = retriever.search("tenant-1", "nonexistent")
        assert results == []

    def test_retrieval_method_label(self) -> None:
        bm25 = BM25Store()
        bm25.add_documents("tenant-1", "en", [("doc-1", 0, "keyword match")])
        graph = KnowledgeGraphStore()

        retriever = HybridRetriever(bm25, graph)
        results = retriever.search("tenant-1", "keyword", search_type=SearchType.BM25)
        if results:
            assert results[0].retrieval_method == "bm25"

    def test_custom_weights(self) -> None:
        bm25 = BM25Store()
        graph = KnowledgeGraphStore()
        retriever = HybridRetriever(
            bm25,
            graph,
            vector_weight=0.2,
            bm25_weight=0.6,
            graph_weight=0.2,
        )
        assert retriever.bm25_weight == 0.6
