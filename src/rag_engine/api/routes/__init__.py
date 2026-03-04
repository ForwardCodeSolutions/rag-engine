"""API route modules."""

from rag_engine.api.routes.documents import router as documents_router
from rag_engine.api.routes.gdpr import router as gdpr_router
from rag_engine.api.routes.health import router as health_router

__all__ = ["documents_router", "gdpr_router", "health_router"]
