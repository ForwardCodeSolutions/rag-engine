"""PDF document parser using PyMuPDF."""

from pathlib import Path

import fitz

from rag_engine.exceptions import IngestionError
from rag_engine.ingestion.parsers.base import BaseParser


class PdfParser(BaseParser):
    """Extract text from PDF files using PyMuPDF (fitz)."""

    def parse(self, file_path: Path) -> str:
        """Extract text from all pages of a PDF file.

        Args:
            file_path: Path to the PDF file.

        Returns:
            Concatenated text from all pages.
        """
        try:
            document = fitz.open(file_path)
        except Exception as exc:
            raise IngestionError(f"Failed to open PDF: {file_path}") from exc

        pages = []
        for page in document:
            text = page.get_text()
            if text.strip():
                pages.append(text)
        document.close()

        if not pages:
            raise IngestionError(f"No text extracted from PDF: {file_path}")

        return "\n\n".join(pages)

    def supported_extensions(self) -> list[str]:
        """Return supported file extensions."""
        return [".pdf"]
