"""FastAPI application setup."""

from fastapi import FastAPI

from rag_engine.api.routes import documents_router, gdpr_router, health_router
from rag_engine.models.config import Settings
from rag_engine.utils.logging import setup_logging

settings = Settings()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    setup_logging(log_level=settings.log_level)

    app = FastAPI(
        title="rag-engine",
        description="Lightweight hybrid RAG engine for multilingual document search",
        version=settings.app_version,
    )

    app.include_router(health_router, prefix="/api/v1")
    app.include_router(documents_router, prefix="/api/v1")
    app.include_router(gdpr_router, prefix="/api/v1")

    return app


app = create_app()
