"""Tests for retrieval quality metrics (RAGAS-style)."""

from rag_engine.core.evaluation import (
    context_precision,
    context_recall,
    evaluate_retrieval,
    f1_score,
    mean_reciprocal_rank,
    ndcg,
)


class TestContextPrecision:
    """Tests for precision@k metric."""

    def test_perfect_precision(self) -> None:
        retrieved = ["a", "b", "c"]
        relevant = {"a", "b", "c"}
        assert context_precision(retrieved, relevant) == 1.0

    def test_half_precision(self) -> None:
        retrieved = ["a", "b", "c", "d"]
        relevant = {"a", "c"}
        assert context_precision(retrieved, relevant) == 0.5

    def test_zero_precision(self) -> None:
        retrieved = ["x", "y", "z"]
        relevant = {"a", "b"}
        assert context_precision(retrieved, relevant) == 0.0

    def test_empty_retrieved(self) -> None:
        assert context_precision([], {"a", "b"}) == 0.0

    def test_empty_relevant(self) -> None:
        assert context_precision(["a", "b"], set()) == 0.0


class TestContextRecall:
    """Tests for recall metric."""

    def test_perfect_recall(self) -> None:
        retrieved = ["a", "b", "c"]
        relevant = {"a", "b"}
        assert context_recall(retrieved, relevant) == 1.0

    def test_partial_recall(self) -> None:
        retrieved = ["a", "x"]
        relevant = {"a", "b", "c"}
        assert abs(context_recall(retrieved, relevant) - 1 / 3) < 1e-6

    def test_zero_recall(self) -> None:
        retrieved = ["x", "y"]
        relevant = {"a", "b"}
        assert context_recall(retrieved, relevant) == 0.0

    def test_empty_relevant(self) -> None:
        assert context_recall(["a"], set()) == 0.0

    def test_empty_retrieved(self) -> None:
        assert context_recall([], {"a"}) == 0.0


class TestMRR:
    """Tests for Mean Reciprocal Rank."""

    def test_first_is_relevant(self) -> None:
        assert mean_reciprocal_rank(["a", "b"], {"a"}) == 1.0

    def test_second_is_relevant(self) -> None:
        assert mean_reciprocal_rank(["x", "a"], {"a"}) == 0.5

    def test_third_is_relevant(self) -> None:
        result = mean_reciprocal_rank(["x", "y", "a"], {"a"})
        assert abs(result - 1 / 3) < 1e-6

    def test_no_relevant(self) -> None:
        assert mean_reciprocal_rank(["x", "y"], {"a"}) == 0.0

    def test_empty_retrieved(self) -> None:
        assert mean_reciprocal_rank([], {"a"}) == 0.0

    def test_multiple_relevant_returns_first(self) -> None:
        result = mean_reciprocal_rank(["x", "a", "b"], {"a", "b"})
        assert result == 0.5


class TestNDCG:
    """Tests for Normalized Discounted Cumulative Gain."""

    def test_perfect_ndcg(self) -> None:
        retrieved = ["a", "b", "c"]
        relevant = {"a", "b", "c"}
        assert abs(ndcg(retrieved, relevant) - 1.0) < 1e-6

    def test_worst_order(self) -> None:
        retrieved = ["x", "y", "a"]
        relevant = {"a"}
        # DCG = 1/log2(4), IDCG = 1/log2(2) = 1.0
        result = ndcg(retrieved, relevant)
        assert 0 < result < 1.0

    def test_zero_ndcg(self) -> None:
        retrieved = ["x", "y", "z"]
        relevant = {"a"}
        assert ndcg(retrieved, relevant) == 0.0

    def test_empty_retrieved(self) -> None:
        assert ndcg([], {"a"}) == 0.0

    def test_empty_relevant(self) -> None:
        assert ndcg(["a"], set()) == 0.0

    def test_single_relevant_at_top(self) -> None:
        assert abs(ndcg(["a", "x"], {"a"}) - 1.0) < 1e-6


class TestF1Score:
    """Tests for F1 score computation."""

    def test_perfect_f1(self) -> None:
        assert f1_score(1.0, 1.0) == 1.0

    def test_zero_f1(self) -> None:
        assert f1_score(0.0, 0.0) == 0.0

    def test_one_zero(self) -> None:
        assert f1_score(1.0, 0.0) == 0.0
        assert f1_score(0.0, 1.0) == 0.0

    def test_balanced_f1(self) -> None:
        result = f1_score(0.5, 0.5)
        assert abs(result - 0.5) < 1e-6


class TestEvaluateRetrieval:
    """Tests for the combined evaluation function."""

    def test_returns_all_metrics(self) -> None:
        result = evaluate_retrieval(["a", "b"], {"a"})
        assert "context_precision" in result
        assert "context_recall" in result
        assert "f1_score" in result
        assert "mrr" in result
        assert "ndcg" in result

    def test_perfect_retrieval(self) -> None:
        result = evaluate_retrieval(["a", "b"], {"a", "b"})
        assert result["context_precision"] == 1.0
        assert result["context_recall"] == 1.0
        assert result["f1_score"] == 1.0
        assert result["mrr"] == 1.0
        assert result["ndcg"] == 1.0

    def test_no_matches(self) -> None:
        result = evaluate_retrieval(["x", "y"], {"a", "b"})
        assert result["context_precision"] == 0.0
        assert result["context_recall"] == 0.0
        assert result["f1_score"] == 0.0
        assert result["mrr"] == 0.0
        assert result["ndcg"] == 0.0

    def test_partial_match_scores(self) -> None:
        result = evaluate_retrieval(["a", "x", "b"], {"a", "b", "c"})
        assert 0 < result["context_precision"] < 1
        assert 0 < result["context_recall"] < 1
        assert 0 < result["f1_score"] < 1
        assert result["mrr"] == 1.0  # first result is relevant
