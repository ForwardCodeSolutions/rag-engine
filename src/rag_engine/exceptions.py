"""Custom exceptions for rag-engine."""


class RagEngineError(Exception):
    """Base exception for all rag-engine errors."""


class DocumentNotFoundError(RagEngineError):
    """Raised when a requested document does not exist."""


class TenantNotFoundError(RagEngineError):
    """Raised when a requested tenant does not exist."""


class IngestionError(RagEngineError):
    """Raised when document ingestion fails."""


class StorageError(RagEngineError):
    """Raised when a storage backend operation fails."""


class SearchError(RagEngineError):
    """Raised when a search operation fails."""
