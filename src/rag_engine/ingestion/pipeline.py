"""Document ingestion pipeline: parse → detect language → chunk."""

from pathlib import Path

import structlog

from rag_engine.exceptions import IngestionError
from rag_engine.ingestion.chunker import (
    BaseChunker,
    Chunk,
    DocumentAwareChunker,
    FixedChunker,
    SemanticChunker,
)
from rag_engine.ingestion.language import detect_language
from rag_engine.ingestion.parsers import DocxParser, PdfParser, TextParser
from rag_engine.ingestion.parsers.base import BaseParser
from rag_engine.models.document import DocumentType

logger = structlog.get_logger()

PARSERS_BY_EXTENSION: dict[str, BaseParser] = {}
for _parser in [PdfParser(), DocxParser(), TextParser()]:
    for _ext in _parser.supported_extensions():
        PARSERS_BY_EXTENSION[_ext] = _parser

CHUNKERS_BY_TYPE: dict[DocumentType, BaseChunker] = {
    DocumentType.GENERAL: SemanticChunker(),
    DocumentType.LEGAL: DocumentAwareChunker(),
    DocumentType.TECHNICAL: DocumentAwareChunker(),
}


def get_parser(file_path: Path) -> BaseParser:
    """Select the appropriate parser based on file extension.

    Args:
        file_path: Path to the document.

    Returns:
        Parser instance for the file type.

    Raises:
        IngestionError: If the file extension is not supported.
    """
    extension = file_path.suffix.lower()
    parser = PARSERS_BY_EXTENSION.get(extension)

    if parser is None:
        supported = ", ".join(sorted(PARSERS_BY_EXTENSION.keys()))
        raise IngestionError(f"Unsupported file extension '{extension}'. Supported: {supported}")

    return parser


def get_chunker(document_type: DocumentType) -> BaseChunker:
    """Select the chunking strategy based on document type.

    Args:
        document_type: Type of document (legal, technical, general).

    Returns:
        Chunker instance for the document type.
    """
    return CHUNKERS_BY_TYPE.get(document_type, FixedChunker())


def ingest_document(
    file_path: Path,
    document_type: DocumentType = DocumentType.GENERAL,
    language_hint: str | None = None,
) -> tuple[list[Chunk], str]:
    """Run the full ingestion pipeline on a document.

    Steps: parse file → detect language → chunk text.

    Args:
        file_path: Path to the document file.
        document_type: Document type for chunking strategy selection.
        language_hint: Optional language override (skips detection).

    Returns:
        Tuple of (list of chunks, detected language code).

    Raises:
        IngestionError: If parsing or chunking fails.
    """
    logger.info(
        "ingestion_started",
        file=str(file_path),
        document_type=document_type,
    )

    parser = get_parser(file_path)
    text = parser.parse(file_path)

    language = language_hint or detect_language(text)

    chunker = get_chunker(document_type)
    chunks = chunker.chunk(text)

    logger.info(
        "ingestion_completed",
        file=str(file_path),
        language=language,
        chunk_count=len(chunks),
    )

    return chunks, language
