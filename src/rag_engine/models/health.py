"""Health check response model."""

from enum import StrEnum

from pydantic import BaseModel, Field


class HealthStatus(StrEnum):
    """Possible health states of the service."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class HealthResponse(BaseModel):
    """Response model for the health check endpoint."""

    status: HealthStatus = Field(description="Overall service health")
    qdrant_connected: bool = Field(description="Qdrant connection status")
    version: str = Field(description="API version")
