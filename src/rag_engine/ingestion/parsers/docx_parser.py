"""DOCX document parser using python-docx."""

from pathlib import Path

from docx import Document

from rag_engine.exceptions import IngestionError
from rag_engine.ingestion.parsers.base import BaseParser


class DocxParser(BaseParser):
    """Extract text from DOCX files using python-docx."""

    def parse(self, file_path: Path) -> str:
        """Extract text from all paragraphs of a DOCX file.

        Args:
            file_path: Path to the DOCX file.

        Returns:
            Concatenated text from all paragraphs.
        """
        try:
            document = Document(str(file_path))
        except Exception as exc:
            raise IngestionError(f"Failed to open DOCX: {file_path}") from exc

        paragraphs = [p.text for p in document.paragraphs if p.text.strip()]

        if not paragraphs:
            raise IngestionError(f"No text extracted from DOCX: {file_path}")

        return "\n\n".join(paragraphs)

    def supported_extensions(self) -> list[str]:
        """Return supported file extensions."""
        return [".docx"]
