"""Smart chunking strategies for document splitting."""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Chunk:
    """A single chunk of text with metadata."""

    text: str
    index: int
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseChunker(ABC):
    """Abstract base class for chunking strategies."""

    @abstractmethod
    def chunk(self, text: str) -> list[Chunk]:
        """Split text into chunks.

        Args:
            text: Full document text.

        Returns:
            List of Chunk objects.
        """


class FixedChunker(BaseChunker):
    """Split text into fixed-size chunks by character count with overlap."""

    def __init__(self, chunk_size: int = 1000, overlap: int = 200) -> None:
        """Initialize with chunk size and overlap.

        Args:
            chunk_size: Maximum characters per chunk.
            overlap: Number of overlapping characters between chunks.

        Raises:
            ValueError: If overlap is not smaller than chunk_size.
        """
        if overlap >= chunk_size:
            raise ValueError(f"overlap ({overlap}) must be less than chunk_size ({chunk_size})")
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[Chunk]:
        """Split text into fixed-size character chunks."""
        if not text.strip():
            return []

        chunks: list[Chunk] = []
        start = 0
        index = 0

        while start < len(text):
            end = start + self.chunk_size
            chunk_text = text[start:end]

            if chunk_text.strip():
                chunks.append(Chunk(text=chunk_text.strip(), index=index))
                index += 1

            start += self.chunk_size - self.overlap

        return chunks


class SemanticChunker(BaseChunker):
    """Split text by paragraphs, merging small ones to reach target size."""

    def __init__(self, min_chunk_size: int = 200, max_chunk_size: int = 1500) -> None:
        """Initialize with size boundaries.

        Args:
            min_chunk_size: Minimum characters per chunk.
            max_chunk_size: Maximum characters per chunk.
        """
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size

    def chunk(self, text: str) -> list[Chunk]:
        """Split text into semantically meaningful chunks by paragraphs."""
        if not text.strip():
            return []

        paragraphs = re.split(r"\n\s*\n", text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        chunks: list[Chunk] = []
        current_parts: list[str] = []
        current_length = 0
        index = 0

        for paragraph in paragraphs:
            if current_length + len(paragraph) > self.max_chunk_size and current_parts:
                chunks.append(Chunk(text="\n\n".join(current_parts), index=index))
                index += 1
                current_parts = []
                current_length = 0

            current_parts.append(paragraph)
            current_length += len(paragraph)

        if current_parts:
            chunks.append(Chunk(text="\n\n".join(current_parts), index=index))

        return chunks


class DocumentAwareChunker(BaseChunker):
    """Split text by document structure: headings, articles, numbered sections."""

    HEADING_PATTERN = re.compile(
        r"^(?:"
        r"#{1,6}\s+"  # Markdown headings
        r"|(?:Article|Section|Chapter|Art\.|Sec\.)\s+\d+"  # Legal/formal headings
        r"|\d+\.\s+[A-Z]"  # Numbered sections like "1. Introduction"
        r")",
        re.MULTILINE | re.IGNORECASE,
    )

    def __init__(self, max_chunk_size: int = 2000) -> None:
        """Initialize with maximum chunk size.

        Args:
            max_chunk_size: Maximum characters per chunk.
        """
        self.max_chunk_size = max_chunk_size

    def chunk(self, text: str) -> list[Chunk]:
        """Split text by structural headings and sections."""
        if not text.strip():
            return []

        split_positions = [match.start() for match in self.HEADING_PATTERN.finditer(text)]

        if not split_positions:
            return SemanticChunker().chunk(text)

        if split_positions[0] != 0:
            split_positions.insert(0, 0)

        sections: list[str] = []
        for i, start in enumerate(split_positions):
            end = split_positions[i + 1] if i + 1 < len(split_positions) else len(text)
            section_text = text[start:end].strip()
            if section_text:
                sections.append(section_text)

        chunks: list[Chunk] = []
        index = 0
        fallback = FixedChunker(chunk_size=self.max_chunk_size, overlap=200)

        for section in sections:
            if len(section) <= self.max_chunk_size:
                chunks.append(Chunk(text=section, index=index))
                index += 1
            else:
                for sub_chunk in fallback.chunk(section):
                    chunks.append(Chunk(text=sub_chunk.text, index=index))
                    index += 1

        return chunks
