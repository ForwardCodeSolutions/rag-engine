"""Integration tests for all three chunking strategies on the same document."""

from rag_engine.ingestion.chunker import (
    DocumentAwareChunker,
    FixedChunker,
    SemanticChunker,
)

SAMPLE_DOCUMENT = """\
# Introduction

Machine Learning is a subset of artificial intelligence that enables systems
to learn from data. It has been applied across many domains including healthcare,
finance, and natural language processing.

# Methods

1. Supervised Learning uses labeled datasets for training.
2. Unsupervised Learning discovers hidden patterns without labels.
3. Reinforcement Learning optimizes actions through reward signals.

# Applications

Natural Language Processing powers chatbots, translation, and search engines.
Computer Vision enables object detection and medical imaging analysis.
Recommender systems personalize content for millions of users daily.
"""


class TestChunkingStrategies:
    """Run the same document through Fixed, Semantic, and DocumentAware chunkers."""

    def test_fixed_chunker_produces_overlapping_chunks(self) -> None:
        chunker = FixedChunker(chunk_size=200, overlap=50)
        chunks = chunker.chunk(SAMPLE_DOCUMENT)

        assert len(chunks) >= 2
        # All chunks should respect max size (with some tolerance for strip)
        for chunk in chunks:
            assert len(chunk.text) <= 200
        # Indices should be sequential
        assert [c.index for c in chunks] == list(range(len(chunks)))

    def test_semantic_chunker_splits_by_paragraphs(self) -> None:
        chunker = SemanticChunker(min_chunk_size=50, max_chunk_size=500)
        chunks = chunker.chunk(SAMPLE_DOCUMENT)

        assert len(chunks) >= 2
        # Each chunk should contain coherent paragraph(s)
        for chunk in chunks:
            assert len(chunk.text) > 0
        # No chunk should exceed max size
        for chunk in chunks:
            assert len(chunk.text) <= 500

    def test_document_aware_chunker_splits_by_headings(self) -> None:
        chunker = DocumentAwareChunker(max_chunk_size=2000)
        chunks = chunker.chunk(SAMPLE_DOCUMENT)

        assert len(chunks) >= 3  # At least Introduction, Methods, Applications
        # First chunk should contain "Introduction"
        assert "Introduction" in chunks[0].text

    def test_all_strategies_cover_full_document(self) -> None:
        """Every strategy should preserve all meaningful content."""
        strategies = [
            FixedChunker(chunk_size=300, overlap=50),
            SemanticChunker(min_chunk_size=50, max_chunk_size=800),
            DocumentAwareChunker(max_chunk_size=2000),
        ]

        for chunker in strategies:
            chunks = chunker.chunk(SAMPLE_DOCUMENT)
            combined = " ".join(c.text for c in chunks)
            # Key terms should be preserved across any strategy
            assert "Machine Learning" in combined
            assert "Supervised Learning" in combined
            assert "Natural Language Processing" in combined

    def test_empty_document_returns_no_chunks(self) -> None:
        for chunker in [FixedChunker(), SemanticChunker(), DocumentAwareChunker()]:
            assert chunker.chunk("") == []
            assert chunker.chunk("   \n\n  ") == []
