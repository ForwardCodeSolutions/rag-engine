"""Shared FastAPI dependencies for authentication and service wiring."""

from fastapi import Header, HTTPException

from rag_engine.models.config import Settings

_settings = Settings()


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
