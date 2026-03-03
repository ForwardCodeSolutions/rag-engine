"""Plain text and Markdown parser."""

from pathlib import Path

from rag_engine.exceptions import IngestionError
from rag_engine.ingestion.parsers.base import BaseParser


class TextParser(BaseParser):
    """Extract text from TXT and Markdown files."""

    def parse(self, file_path: Path) -> str:
        """Read text content from a plain text or Markdown file.

        Args:
            file_path: Path to the text file.

        Returns:
            File content as a string.
        """
        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            try:
                content = file_path.read_text(encoding="latin-1")
            except Exception as exc:
                raise IngestionError(f"Failed to read file: {file_path}") from exc
        except Exception as exc:
            raise IngestionError(f"Failed to read file: {file_path}") from exc

        if not content.strip():
            raise IngestionError(f"File is empty: {file_path}")

        return content

    def supported_extensions(self) -> list[str]:
        """Return supported file extensions."""
        return [".txt", ".md"]
