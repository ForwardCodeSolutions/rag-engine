"""Score normalization and weighted re-ranking for hybrid retrieval."""

from dataclasses import dataclass


@dataclass
class ScoredChunk:
    """A chunk with scores from one or more retrieval methods."""

    document_id: str
    chunk_index: int
    text: str
    vector_score: float = 0.0
    bm25_score: float = 0.0
    graph_score: float = 0.0
    combined_score: float = 0.0


def normalize_scores(scores: list[float]) -> list[float]:
    """Normalize a list of scores to the [0, 1] range using min-max scaling.

    Args:
        scores: Raw scores from a retrieval method.

    Returns:
        Normalized scores. Returns all zeros if input is empty
        or all values are equal.
    """
    if not scores:
        return []

    min_score = min(scores)
    max_score = max(scores)
    score_range = max_score - min_score

    if score_range == 0:
        return [1.0] * len(scores)

    return [(s - min_score) / score_range for s in scores]


def rerank(
    chunks: list[ScoredChunk],
    vector_weight: float = 0.5,
    bm25_weight: float = 0.3,
    graph_weight: float = 0.2,
) -> list[ScoredChunk]:
    """Compute combined scores and sort chunks by relevance.

    Normalizes each score dimension independently, then combines
    them using the provided weights.

    Args:
        chunks: Chunks with raw scores from retrieval methods.
        vector_weight: Weight for vector similarity scores.
        bm25_weight: Weight for BM25 keyword scores.
        graph_weight: Weight for knowledge graph scores.

    Returns:
        Chunks sorted by combined_score descending.
    """
    if not chunks:
        return []

    # Normalize each score dimension
    vector_raw = [c.vector_score for c in chunks]
    bm25_raw = [c.bm25_score for c in chunks]
    graph_raw = [c.graph_score for c in chunks]

    vector_norm = normalize_scores(vector_raw)
    bm25_norm = normalize_scores(bm25_raw)
    graph_norm = normalize_scores(graph_raw)

    for i, chunk in enumerate(chunks):
        chunk.combined_score = (
            vector_weight * vector_norm[i]
            + bm25_weight * bm25_norm[i]
            + graph_weight * graph_norm[i]
        )

    chunks.sort(key=lambda c: c.combined_score, reverse=True)
    return chunks
