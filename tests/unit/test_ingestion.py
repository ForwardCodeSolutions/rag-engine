"""Tests for document ingestion pipeline."""

from pathlib import Path

import pytest

from rag_engine.exceptions import IngestionError
from rag_engine.ingestion.chunker import (
    Chunk,
    DocumentAwareChunker,
    FixedChunker,
    SemanticChunker,
)
from rag_engine.ingestion.language import detect_language
from rag_engine.ingestion.parsers.text_parser import TextParser
from rag_engine.ingestion.pipeline import get_chunker, get_parser, ingest_document
from rag_engine.models.document import DocumentType


class TestTextParser:
    """Tests for plain text and Markdown parser."""

    def test_parse_txt_file(self, tmp_path: Path) -> None:
        file = tmp_path / "test.txt"
        file.write_text("Hello, world!", encoding="utf-8")
        parser = TextParser()
        result = parser.parse(file)
        assert result == "Hello, world!"

    def test_parse_md_file(self, tmp_path: Path) -> None:
        file = tmp_path / "readme.md"
        file.write_text("# Title\n\nSome content.", encoding="utf-8")
        parser = TextParser()
        result = parser.parse(file)
        assert "# Title" in result

    def test_parse_empty_file_raises(self, tmp_path: Path) -> None:
        file = tmp_path / "empty.txt"
        file.write_text("", encoding="utf-8")
        parser = TextParser()
        with pytest.raises(IngestionError, match="empty"):
            parser.parse(file)

    def test_supported_extensions(self) -> None:
        parser = TextParser()
        assert ".txt" in parser.supported_extensions()
        assert ".md" in parser.supported_extensions()


class TestFixedChunker:
    """Tests for fixed-size chunker."""

    def test_short_text_single_chunk(self) -> None:
        chunker = FixedChunker(chunk_size=100, overlap=20)
        chunks = chunker.chunk("Short text.")
        assert len(chunks) == 1
        assert chunks[0].text == "Short text."

    def test_long_text_multiple_chunks(self) -> None:
        chunker = FixedChunker(chunk_size=50, overlap=10)
        text = "A" * 120
        chunks = chunker.chunk(text)
        assert len(chunks) > 1

    def test_empty_text_no_chunks(self) -> None:
        chunker = FixedChunker()
        chunks = chunker.chunk("")
        assert chunks == []

    def test_chunk_index_sequential(self) -> None:
        chunker = FixedChunker(chunk_size=50, overlap=10)
        chunks = chunker.chunk("A" * 200)
        indexes = [c.index for c in chunks]
        assert indexes == list(range(len(chunks)))


class TestSemanticChunker:
    """Tests for semantic paragraph-based chunker."""

    def test_splits_by_paragraphs(self) -> None:
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        chunker = SemanticChunker(min_chunk_size=5, max_chunk_size=40)
        chunks = chunker.chunk(text)
        assert len(chunks) >= 2

    def test_merges_small_paragraphs(self) -> None:
        text = "A.\n\nB.\n\nC."
        chunker = SemanticChunker(min_chunk_size=5, max_chunk_size=1000)
        chunks = chunker.chunk(text)
        assert len(chunks) == 1

    def test_empty_text_no_chunks(self) -> None:
        chunker = SemanticChunker()
        assert chunker.chunk("") == []


class TestDocumentAwareChunker:
    """Tests for structure-aware chunker."""

    def test_splits_by_headings(self) -> None:
        text = "# Introduction\n\nSome intro text.\n\n# Methods\n\nSome methods text."
        chunker = DocumentAwareChunker()
        chunks = chunker.chunk(text)
        assert len(chunks) == 2
        assert "Introduction" in chunks[0].text
        assert "Methods" in chunks[1].text

    def test_splits_by_numbered_sections(self) -> None:
        text = "1. Overview\n\nDetails here.\n\n2. Architecture\n\nMore details."
        chunker = DocumentAwareChunker()
        chunks = chunker.chunk(text)
        assert len(chunks) == 2

    def test_falls_back_to_semantic_without_headings(self) -> None:
        text = "Just plain text.\n\nAnother paragraph.\n\nThird paragraph."
        chunker = DocumentAwareChunker()
        chunks = chunker.chunk(text)
        assert len(chunks) >= 1

    def test_empty_text_no_chunks(self) -> None:
        chunker = DocumentAwareChunker()
        assert chunker.chunk("") == []


class TestLanguageDetection:
    """Tests for language detection."""

    def test_detect_english(self) -> None:
        text = "This is a sample English document with enough words for detection."
        assert detect_language(text) == "en"

    def test_detect_italian(self) -> None:
        text = "Questo è un documento di esempio in lingua italiana con abbastanza parole."
        assert detect_language(text) == "it"

    def test_detect_russian(self) -> None:
        text = "Это пример документа на русском языке с достаточным количеством слов."
        assert detect_language(text) == "ru"

    def test_empty_text_returns_fallback(self) -> None:
        assert detect_language("") == "en"


class TestPipeline:
    """Tests for the ingestion pipeline."""

    def test_get_parser_txt(self) -> None:
        parser = get_parser(Path("document.txt"))
        assert isinstance(parser, TextParser)

    def test_get_parser_unsupported_raises(self) -> None:
        with pytest.raises(IngestionError, match="Unsupported"):
            get_parser(Path("file.xyz"))

    def test_get_chunker_returns_correct_type(self) -> None:
        chunker = get_chunker(DocumentType.GENERAL)
        assert isinstance(chunker, SemanticChunker)
        chunker = get_chunker(DocumentType.LEGAL)
        assert isinstance(chunker, DocumentAwareChunker)

    def test_ingest_document_full_pipeline(self, tmp_path: Path) -> None:
        file = tmp_path / "test.txt"
        file.write_text(
            "This is a test document in English.\n\nIt has multiple paragraphs.\n\n"
            "The third paragraph provides more content for the chunker.",
            encoding="utf-8",
        )
        chunks, language = ingest_document(file)
        assert len(chunks) >= 1
        assert language == "en"
        assert all(isinstance(c, Chunk) for c in chunks)

    def test_ingest_with_language_hint(self, tmp_path: Path) -> None:
        file = tmp_path / "doc.txt"
        file.write_text("Some content here.", encoding="utf-8")
        chunks, language = ingest_document(file, language_hint="it")
        assert language == "it"

    def test_ingest_legal_document(self, tmp_path: Path) -> None:
        file = tmp_path / "contract.txt"
        file.write_text(
            "Article 1\n\nParty obligations.\n\nArticle 2\n\nPayment terms.",
            encoding="utf-8",
        )
        chunks, language = ingest_document(file, document_type=DocumentType.LEGAL)
        assert len(chunks) >= 2
