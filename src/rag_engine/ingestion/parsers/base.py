"""Abstract base parser for document extraction."""

from abc import ABC, abstractmethod
from pathlib import Path


class BaseParser(ABC):
    """Base class for all document parsers."""

    @abstractmethod
    def parse(self, file_path: Path) -> str:
        """Extract text content from a file.

        Args:
            file_path: Path to the document file.

        Returns:
            Extracted text as a single string.

        Raises:
            IngestionError: If the file cannot be parsed.
        """

    @abstractmethod
    def supported_extensions(self) -> list[str]:
        """Return list of file extensions this parser supports.

        Returns:
            List of extensions including the dot, e.g. [".pdf"].
        """
