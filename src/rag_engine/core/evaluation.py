"""Retrieval quality metrics inspired by RAGAS.

Provides evaluation functions for measuring retrieval effectiveness
without requiring LLM calls. Focuses on information-retrieval metrics
that can be computed from ground-truth relevance judgments.
"""

import math


def context_precision(
    retrieved_ids: list[str],
    relevant_ids: set[str],
) -> float:
    """Compute precision@k: fraction of retrieved documents that are relevant.

    Args:
        retrieved_ids: Ordered list of retrieved document IDs.
        relevant_ids: Set of ground-truth relevant document IDs.

    Returns:
        Precision score in [0, 1]. Returns 0.0 if nothing was retrieved.
    """
    if not retrieved_ids:
        return 0.0

    relevant_count = sum(1 for doc_id in retrieved_ids if doc_id in relevant_ids)
    return relevant_count / len(retrieved_ids)


def context_recall(
    retrieved_ids: list[str],
    relevant_ids: set[str],
) -> float:
    """Compute recall: fraction of relevant documents that were retrieved.

    Args:
        retrieved_ids: Ordered list of retrieved document IDs.
        relevant_ids: Set of ground-truth relevant document IDs.

    Returns:
        Recall score in [0, 1]. Returns 0.0 if there are no relevant documents.
    """
    if not relevant_ids:
        return 0.0

    retrieved_set = set(retrieved_ids)
    found = sum(1 for doc_id in relevant_ids if doc_id in retrieved_set)
    return found / len(relevant_ids)


def mean_reciprocal_rank(
    retrieved_ids: list[str],
    relevant_ids: set[str],
) -> float:
    """Compute Mean Reciprocal Rank (MRR).

    MRR is 1/rank of the first relevant document in the retrieved list.

    Args:
        retrieved_ids: Ordered list of retrieved document IDs.
        relevant_ids: Set of ground-truth relevant document IDs.

    Returns:
        MRR score in [0, 1]. Returns 0.0 if no relevant document is found.
    """
    for rank, doc_id in enumerate(retrieved_ids, start=1):
        if doc_id in relevant_ids:
            return 1.0 / rank
    return 0.0


def ndcg(
    retrieved_ids: list[str],
    relevant_ids: set[str],
) -> float:
    """Compute Normalized Discounted Cumulative Gain (nDCG).

    Uses binary relevance (1 if relevant, 0 otherwise).

    Args:
        retrieved_ids: Ordered list of retrieved document IDs.
        relevant_ids: Set of ground-truth relevant document IDs.

    Returns:
        nDCG score in [0, 1]. Returns 0.0 if no relevant documents exist
        or nothing was retrieved.
    """
    if not retrieved_ids or not relevant_ids:
        return 0.0

    # DCG: sum of relevance / log2(rank + 1)
    dcg = 0.0
    for rank, doc_id in enumerate(retrieved_ids, start=1):
        if doc_id in relevant_ids:
            dcg += 1.0 / math.log2(rank + 1)

    # Ideal DCG: all relevant docs at top positions
    ideal_count = min(len(relevant_ids), len(retrieved_ids))
    idcg = sum(1.0 / math.log2(rank + 1) for rank in range(1, ideal_count + 1))

    if idcg == 0.0:
        return 0.0

    return dcg / idcg


def f1_score(precision: float, recall: float) -> float:
    """Compute F1 score from precision and recall.

    Args:
        precision: Precision value in [0, 1].
        recall: Recall value in [0, 1].

    Returns:
        F1 score in [0, 1]. Returns 0.0 if both precision and recall are 0.
    """
    if precision + recall == 0.0:
        return 0.0
    return 2 * (precision * recall) / (precision + recall)


def evaluate_retrieval(
    retrieved_ids: list[str],
    relevant_ids: set[str],
) -> dict[str, float]:
    """Compute all retrieval quality metrics at once.

    Args:
        retrieved_ids: Ordered list of retrieved document IDs.
        relevant_ids: Set of ground-truth relevant document IDs.

    Returns:
        Dictionary with all metric names and their values.
    """
    prec = context_precision(retrieved_ids, relevant_ids)
    rec = context_recall(retrieved_ids, relevant_ids)

    return {
        "context_precision": round(prec, 4),
        "context_recall": round(rec, 4),
        "f1_score": round(f1_score(prec, rec), 4),
        "mrr": round(mean_reciprocal_rank(retrieved_ids, relevant_ids), 4),
        "ndcg": round(ndcg(retrieved_ids, relevant_ids), 4),
    }
