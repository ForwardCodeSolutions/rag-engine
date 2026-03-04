"""Tests for document parsers using fixture files."""

from pathlib import Path

import pytest

from rag_engine.exceptions import IngestionError
from rag_engine.ingestion.parsers.docx_parser import DocxParser
from rag_engine.ingestion.parsers.pdf_parser import PdfParser
from rag_engine.ingestion.parsers.text_parser import TextParser

FIXTURES = Path(__file__).parent.parent / "fixtures"


class TestPdfParser:
    """Tests for PDF parser with fixture files."""

    def setup_method(self) -> None:
        self.parser = PdfParser()

    def test_parse_sample_pdf(self) -> None:
        text = self.parser.parse(FIXTURES / "sample.pdf")
        assert len(text) > 0
        assert "PDF" in text or "document" in text.lower() or "sample" in text.lower()

    def test_supported_extensions(self) -> None:
        assert ".pdf" in self.parser.supported_extensions()

    def test_parse_nonexistent_file_raises(self) -> None:
        with pytest.raises(IngestionError, match="Failed to open PDF"):
            self.parser.parse(FIXTURES / "nonexistent.pdf")

    def test_parse_corrupted_file_raises(self, tmp_path: Path) -> None:
        bad_file = tmp_path / "bad.pdf"
        bad_file.write_bytes(b"not a real pdf")
        with pytest.raises(IngestionError):
            self.parser.parse(bad_file)


class TestDocxParser:
    """Tests for DOCX parser with fixture files."""

    def setup_method(self) -> None:
        self.parser = DocxParser()

    def test_parse_sample_docx(self) -> None:
        text = self.parser.parse(FIXTURES / "sample.docx")
        assert len(text) > 0
        assert "sample" in text.lower() or "document" in text.lower()

    def test_docx_contains_expected_content(self) -> None:
        text = self.parser.parse(FIXTURES / "sample.docx")
        assert "GDPR" in text

    def test_supported_extensions(self) -> None:
        assert ".docx" in self.parser.supported_extensions()

    def test_parse_nonexistent_file_raises(self) -> None:
        with pytest.raises(IngestionError, match="Failed to open DOCX"):
            self.parser.parse(FIXTURES / "nonexistent.docx")

    def test_parse_corrupted_file_raises(self, tmp_path: Path) -> None:
        bad_file = tmp_path / "bad.docx"
        bad_file.write_bytes(b"not a real docx")
        with pytest.raises(IngestionError):
            self.parser.parse(bad_file)

    def test_parse_empty_docx_raises(self, tmp_path: Path) -> None:
        from docx import Document

        empty_file = tmp_path / "empty.docx"
        doc = Document()
        doc.save(empty_file)
        with pytest.raises(IngestionError, match="No text extracted"):
            self.parser.parse(empty_file)


class TestTextParser:
    """Tests for text parser."""

    def setup_method(self) -> None:
        self.parser = TextParser()

    def test_parse_txt_file(self, tmp_path: Path) -> None:
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Hello world from a test file.")
        text = self.parser.parse(txt_file)
        assert "Hello world" in text

    def test_parse_md_file(self, tmp_path: Path) -> None:
        md_file = tmp_path / "readme.md"
        md_file.write_text("# Title\n\nContent here.")
        text = self.parser.parse(md_file)
        assert "Title" in text

    def test_supported_extensions(self) -> None:
        exts = self.parser.supported_extensions()
        assert ".txt" in exts
        assert ".md" in exts

    def test_parse_nonexistent_file_raises(self) -> None:
        with pytest.raises(IngestionError):
            self.parser.parse(Path("/nonexistent/file.txt"))
