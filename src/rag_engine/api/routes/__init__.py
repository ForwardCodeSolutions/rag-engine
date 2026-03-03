"""API route modules."""

from rag_engine.api.routes.gdpr import router as gdpr_router
from rag_engine.api.routes.health import router as health_router

__all__ = ["gdpr_router", "health_router"]
