"""BM25 keyword search index with per-tenant and per-language isolation."""

from dataclasses import dataclass, field

import structlog
from rank_bm25 import BM25Plus

logger = structlog.get_logger()


@dataclass
class IndexedDocument:
    """A document stored in the BM25 index."""

    document_id: str
    chunk_index: int
    text: str
    tokens: list[str]


def tokenize(text: str) -> list[str]:
    """Split text into lowercase tokens for BM25 indexing.

    Args:
        text: Raw text to tokenize.

    Returns:
        List of lowercase word tokens.
    """
    return text.lower().split()


@dataclass
class _LanguageIndex:
    """BM25 index for a single language within a tenant."""

    documents: list[IndexedDocument] = field(default_factory=list)
    bm25: BM25Plus | None = None

    def rebuild(self) -> None:
        """Rebuild the BM25 index from stored documents."""
        if self.documents:
            corpus = [doc.tokens for doc in self.documents]
            self.bm25 = BM25Plus(corpus)
        else:
            self.bm25 = None


class BM25Store:
    """In-memory BM25 index with per-tenant and per-language isolation.

    Each tenant has independent indexes per language, ensuring that
    BM25 tokenization stays language-appropriate and tenant data
    never leaks across boundaries.
    """

    def __init__(self) -> None:
        self._indexes: dict[str, dict[str, _LanguageIndex]] = {}

    def _get_index(self, tenant_id: str, language: str) -> _LanguageIndex:
        """Get or create a language index for a tenant."""
        if tenant_id not in self._indexes:
            self._indexes[tenant_id] = {}
        if language not in self._indexes[tenant_id]:
            self._indexes[tenant_id][language] = _LanguageIndex()
        return self._indexes[tenant_id][language]

    def add_documents(
        self,
        tenant_id: str,
        language: str,
        chunks: list[tuple[str, int, str]],
    ) -> int:
        """Add document chunks to the BM25 index.

        Args:
            tenant_id: Tenant identifier for isolation.
            language: Language code (e.g. "en", "it", "ru").
            chunks: List of (document_id, chunk_index, text) tuples.

        Returns:
            Number of chunks indexed.
        """
        index = self._get_index(tenant_id, language)

        for document_id, chunk_index, text in chunks:
            tokens = tokenize(text)
            if not tokens:
                continue
            index.documents.append(
                IndexedDocument(
                    document_id=document_id,
                    chunk_index=chunk_index,
                    text=text,
                    tokens=tokens,
                )
            )

        index.rebuild()

        logger.info(
            "bm25_documents_added",
            tenant_id=tenant_id,
            language=language,
            chunks_added=len(chunks),
            total_documents=len(index.documents),
        )

        return len(chunks)

    def search(
        self,
        tenant_id: str,
        query: str,
        language: str,
        top_k: int = 10,
    ) -> list[tuple[str, int, str, float]]:
        """Search the BM25 index for a tenant and language.

        Args:
            tenant_id: Tenant identifier.
            query: Search query text.
            language: Language code to search within.
            top_k: Maximum number of results to return.

        Returns:
            List of (document_id, chunk_index, text, score) tuples,
            sorted by descending score.
        """
        index = self._get_index(tenant_id, language)

        if not index.documents or index.bm25 is None:
            return []

        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        scores = index.bm25.get_scores(query_tokens)

        scored_results = [
            (doc.document_id, doc.chunk_index, doc.text, float(score))
            for doc, score in zip(index.documents, scores, strict=True)
            if score > 0
        ]

        scored_results.sort(key=lambda r: r[3], reverse=True)

        return scored_results[:top_k]

    def remove_document(self, tenant_id: str, document_id: str) -> int:
        """Remove all chunks of a document from all language indexes of a tenant.

        Args:
            tenant_id: Tenant identifier.
            document_id: Document to remove.

        Returns:
            Number of chunks removed.
        """
        if tenant_id not in self._indexes:
            return 0

        total_removed = 0

        for language, index in self._indexes[tenant_id].items():
            before = len(index.documents)
            index.documents = [doc for doc in index.documents if doc.document_id != document_id]
            removed = before - len(index.documents)
            total_removed += removed

            if removed > 0:
                index.rebuild()
                logger.info(
                    "bm25_document_removed",
                    tenant_id=tenant_id,
                    language=language,
                    document_id=document_id,
                    chunks_removed=removed,
                )

        return total_removed

    def clear_tenant(self, tenant_id: str) -> None:
        """Remove all data for a tenant (GDPR right to erasure).

        Args:
            tenant_id: Tenant whose data should be deleted.
        """
        if tenant_id in self._indexes:
            del self._indexes[tenant_id]
            logger.info("bm25_tenant_cleared", tenant_id=tenant_id)

    def clear(self) -> None:
        """Remove all data from all indexes."""
        self._indexes.clear()
        logger.info("bm25_all_cleared")
