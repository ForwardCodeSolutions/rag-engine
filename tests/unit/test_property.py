"""Property-based tests using Hypothesis."""

import re

from hypothesis import given, settings
from hypothesis import strategies as st

from rag_engine.core.reranker import ScoredChunk, normalize_scores, rerank
from rag_engine.ingestion.chunker import FixedChunker, SemanticChunker
from rag_engine.models.search import SearchQuery
from rag_engine.storage.bm25_store import BM25Store

# --- Chunker properties ---


@given(text=st.text(min_size=1).filter(lambda t: t.strip()))
@settings(max_examples=100)
def test_fixed_chunker_preserves_content(text: str) -> None:
    """Every non-whitespace character from the original text must appear in the chunks."""
    chunker = FixedChunker(chunk_size=50, overlap=10)
    chunks = chunker.chunk(text)

    if not chunks:
        return

    joined = "".join(c.text for c in chunks)
    # Every non-whitespace character from original must appear in joined chunks
    for char in text:
        if not char.isspace():
            assert char in joined, f"Lost character: {char!r}"


@given(chunk_size=st.integers(min_value=2, max_value=500))
@settings(max_examples=50)
def test_fixed_chunker_respects_size(chunk_size: int) -> None:
    """Each chunk must not exceed chunk_size (before stripping)."""
    overlap = min(chunk_size - 1, max(1, chunk_size // 5))
    chunker = FixedChunker(chunk_size=chunk_size, overlap=overlap)
    text = "word " * 200  # predictable text
    chunks = chunker.chunk(text)

    for chunk in chunks:
        # Raw slice is chunk_size chars; stripping may shorten it
        assert len(chunk.text) <= chunk_size


@given(text=st.text(min_size=1).filter(lambda t: t.strip()))
@settings(max_examples=100)
def test_semantic_chunker_preserves_content(text: str) -> None:
    """Semantic chunker should not lose any paragraph content."""
    chunker = SemanticChunker(min_chunk_size=10, max_chunk_size=200)
    chunks = chunker.chunk(text)

    if not chunks:
        return

    joined = "\n\n".join(c.text for c in chunks)
    for para in re.split(r"\n\s*\n", text):
        para = para.strip()
        if para:
            assert para in joined


# --- SearchQuery model ---


@given(query=st.text(min_size=1, max_size=500).filter(lambda t: t.strip()))
@settings(max_examples=100)
def test_search_query_accepts_any_query(query: str) -> None:
    """SearchQuery should accept any non-empty query up to 500 chars."""
    sq = SearchQuery(query=query, tenant_id="test-tenant")
    assert sq.query == query


# --- Reranker / normalize_scores ---


@given(scores=st.lists(st.floats(min_value=0, max_value=1e6, allow_nan=False), min_size=1))
@settings(max_examples=100)
def test_normalize_scores_in_range(scores: list[float]) -> None:
    """Normalized scores must always be in [0, 1]."""
    result = normalize_scores(scores)
    assert len(result) == len(scores)
    for s in result:
        assert 0.0 <= s <= 1.0


@given(
    scores=st.lists(
        st.floats(min_value=0, max_value=1e6, allow_nan=False, allow_infinity=False),
        min_size=1,
        max_size=20,
    )
)
@settings(max_examples=100)
def test_reranker_combined_scores_in_range(scores: list[float]) -> None:
    """Combined scores after reranking must be in [0, 1]."""
    chunks = [
        ScoredChunk(
            document_id=f"doc-{i}",
            chunk_index=i,
            text=f"chunk {i}",
            vector_score=s,
            bm25_score=s,
            graph_score=s,
        )
        for i, s in enumerate(scores)
    ]
    result = rerank(chunks)
    for chunk in result:
        assert 0.0 <= chunk.combined_score <= 1.0 + 1e-9


# --- BM25Store ---


@given(query=st.text(min_size=3, max_size=50, alphabet=st.characters(whitelist_categories=("L",))))
@settings(max_examples=50)
def test_bm25_exact_match_returns_results(query: str) -> None:
    """BM25 search for text that was indexed must return at least one result."""
    store = BM25Store()
    text = f"prefix {query} suffix"
    store.add_documents("t1", "en", [("doc-1", 0, text)])
    results = store.search("t1", query, "en", top_k=5)
    assert len(results) >= 1
    assert results[0][0] == "doc-1"


# --- ID validation ---


@given(id_str=st.from_regex(r"^[a-zA-Z0-9_-]{1,128}$", fullmatch=True))
@settings(max_examples=100)
def test_tenant_id_validation(id_str: str) -> None:
    """Any string matching the tenant_id pattern should be accepted."""
    sq = SearchQuery(query="test query", tenant_id=id_str)
    assert sq.tenant_id == id_str


@given(
    id_str=st.text(min_size=1, max_size=20).filter(lambda s: not re.match(r"^[a-zA-Z0-9_-]+$", s))
)
@settings(max_examples=50)
def test_tenant_id_rejects_invalid(id_str: str) -> None:
    """Strings with invalid characters should be rejected."""
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        SearchQuery(query="test", tenant_id=id_str)
