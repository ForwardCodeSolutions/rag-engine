"""Shared FastAPI dependencies for authentication and service wiring."""

import re
from functools import lru_cache

import structlog
from fastapi import Header, HTTPException

from rag_engine.models.config import Settings
from rag_engine.services.gdpr import GDPRService
from rag_engine.storage.bm25_store import BM25Store
from rag_engine.storage.knowledge_graph import KnowledgeGraphStore
from rag_engine.storage.qdrant_store import QdrantStore

_settings = Settings()
_logger = structlog.get_logger()

VALID_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,128}$")


@lru_cache(maxsize=1)
def get_gdpr_service() -> GDPRService:
    """Factory for GDPRService with all storage backends."""
    qdrant_store: QdrantStore | None = None
    try:
        qdrant_store = QdrantStore(url=_settings.qdrant_url)
        qdrant_store._client.get_collections()  # verify connectivity
    except Exception:
        _logger.warning("qdrant_unavailable_for_gdpr", url=_settings.qdrant_url)
        qdrant_store = None
    return GDPRService(BM25Store(), KnowledgeGraphStore(), qdrant_store)


async def verify_api_key(x_api_key: str = Header(...)) -> str:
    """Validate X-API-Key header against configured API key.

    Args:
        x_api_key: API key from request header.

    Returns:
        The validated API key.

    Raises:
        HTTPException: 401 if key is missing or invalid.
    """
    if x_api_key != _settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


def validate_id(value: str, name: str) -> str:
    """Validate that an ID matches the allowed pattern.

    Args:
        value: The ID string to validate.
        name: Human-readable name for error messages.

    Returns:
        The validated ID string.

    Raises:
        HTTPException: 400 if the ID is invalid.
    """
    if not VALID_ID_PATTERN.match(value):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid {name}: must be 1-128 alphanumeric, dash, or underscore characters",
        )
    return value
