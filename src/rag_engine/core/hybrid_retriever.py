"""Hybrid retriever combining Vector, BM25, and Knowledge Graph search."""

import structlog

from rag_engine.core.reranker import ScoredChunk, rerank
from rag_engine.models.search import SearchResult, SearchType
from rag_engine.storage.bm25_store import BM25Store
from rag_engine.storage.knowledge_graph import KnowledgeGraphStore

logger = structlog.get_logger()

# Type alias for raw results from storage backends
RawResult = tuple[str, int, str, float]


class HybridRetriever:
    """Combines results from BM25 and Knowledge Graph with weighted re-ranking.

    Vector search (Qdrant) results can be passed in externally since
    Qdrant requires async client calls. This retriever handles merging,
    deduplication, normalization, and final ranking.
    """

    def __init__(
        self,
        bm25_store: BM25Store,
        graph_store: KnowledgeGraphStore,
        vector_weight: float = 0.5,
        bm25_weight: float = 0.3,
        graph_weight: float = 0.2,
    ) -> None:
        """Initialize with storage backends and retrieval weights.

        Args:
            bm25_store: BM25 keyword search index.
            graph_store: Knowledge graph store.
            vector_weight: Weight for vector similarity scores.
            bm25_weight: Weight for BM25 keyword scores.
            graph_weight: Weight for knowledge graph scores.
        """
        self.bm25_store = bm25_store
        self.graph_store = graph_store
        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight
        self.graph_weight = graph_weight

    def _chunk_key(self, document_id: str, chunk_index: int) -> str:
        """Create a unique key for deduplication."""
        return f"{document_id}:{chunk_index}"

    def search(
        self,
        tenant_id: str,
        query: str,
        language: str = "en",
        top_k: int = 10,
        search_type: SearchType = SearchType.HYBRID,
        vector_results: list[RawResult] | None = None,
    ) -> list[SearchResult]:
        """Execute hybrid search across configured retrieval methods.

        Args:
            tenant_id: Tenant identifier.
            query: Search query text.
            language: Language code for BM25 index selection.
            top_k: Maximum number of results to return.
            search_type: Which retrieval method(s) to use.
            vector_results: Pre-computed vector search results
                (document_id, chunk_index, text, score).

        Returns:
            List of SearchResult models, sorted by combined score.
        """
        if vector_results is None:
            vector_results = []

        bm25_results: list[RawResult] = []
        graph_results: list[RawResult] = []

        if search_type in (SearchType.HYBRID, SearchType.BM25):
            bm25_results = self.bm25_store.search(
                tenant_id=tenant_id,
                query=query,
                language=language,
                top_k=top_k * 2,
            )

        if search_type in (SearchType.HYBRID, SearchType.GRAPH):
            graph_results = self.graph_store.search(
                tenant_id=tenant_id,
                query=query,
                top_k=top_k * 2,
            )

        if search_type == SearchType.VECTOR:
            bm25_results = []
            graph_results = []

        # Merge all results into ScoredChunks with deduplication
        merged = self._merge_results(vector_results, bm25_results, graph_results)

        if not merged:
            return []

        # Re-rank with configured weights
        ranked = rerank(
            list(merged.values()),
            vector_weight=self.vector_weight,
            bm25_weight=self.bm25_weight,
            graph_weight=self.graph_weight,
        )

        # Convert to SearchResult models
        results: list[SearchResult] = []
        for chunk in ranked[:top_k]:
            method = self._determine_method(chunk)
            results.append(
                SearchResult(
                    document_id=chunk.document_id,
                    chunk_text=chunk.text,
                    score=round(chunk.combined_score, 4),
                    retrieval_method=method,
                )
            )

        logger.info(
            "hybrid_search_completed",
            tenant_id=tenant_id,
            search_type=search_type,
            vector_count=len(vector_results),
            bm25_count=len(bm25_results),
            graph_count=len(graph_results),
            merged_count=len(merged),
            returned_count=len(results),
        )

        return results

    def _merge_results(
        self,
        vector_results: list[RawResult],
        bm25_results: list[RawResult],
        graph_results: list[RawResult],
    ) -> dict[str, ScoredChunk]:
        """Merge results from all sources with deduplication.

        When the same chunk appears in multiple sources, scores
        are accumulated into a single ScoredChunk.

        Args:
            vector_results: Results from vector search.
            bm25_results: Results from BM25 search.
            graph_results: Results from knowledge graph search.

        Returns:
            Dictionary of chunk_key -> ScoredChunk.
        """
        merged: dict[str, ScoredChunk] = {}

        for doc_id, chunk_idx, text, score in vector_results:
            key = self._chunk_key(doc_id, chunk_idx)
            if key not in merged:
                merged[key] = ScoredChunk(document_id=doc_id, chunk_index=chunk_idx, text=text)
            merged[key].vector_score = score

        for doc_id, chunk_idx, text, score in bm25_results:
            key = self._chunk_key(doc_id, chunk_idx)
            if key not in merged:
                merged[key] = ScoredChunk(document_id=doc_id, chunk_index=chunk_idx, text=text)
            merged[key].bm25_score = score

        for doc_id, chunk_idx, text, score in graph_results:
            key = self._chunk_key(doc_id, chunk_idx)
            if key not in merged:
                merged[key] = ScoredChunk(document_id=doc_id, chunk_index=chunk_idx, text=text)
            merged[key].graph_score = score

        return merged

    def _determine_method(self, chunk: ScoredChunk) -> str:
        """Determine which retrieval method contributed most to a result."""
        scores = {
            "vector": chunk.vector_score,
            "bm25": chunk.bm25_score,
            "graph": chunk.graph_score,
        }
        active = {k: v for k, v in scores.items() if v > 0}

        if not active:
            return "hybrid"
        if len(active) > 1:
            return "hybrid"
        return next(iter(active))
