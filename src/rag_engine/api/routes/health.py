"""Health check endpoint."""

from fastapi import APIRouter

from rag_engine.models.config import Settings
from rag_engine.models.health import HealthResponse, HealthStatus

router = APIRouter(tags=["system"])
settings = Settings()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Return current service health status."""
    return HealthResponse(
        status=HealthStatus.HEALTHY,
        qdrant_connected=False,
        version=settings.app_version,
    )
