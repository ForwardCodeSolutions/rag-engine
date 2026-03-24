"""FastAPI application setup."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from rag_engine.api.routes import documents_router, gdpr_router, health_router
from rag_engine.api.routes.rate_limit import limiter
from rag_engine.models.config import Settings
from rag_engine.utils.logging import setup_logging

settings = Settings()  # type: ignore[call-arg]
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application startup and shutdown lifecycle."""
    setup_logging(log_level=settings.log_level)
    logger.info("app_started", version=settings.app_version)
    yield
    logger.info("app_shutdown")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="rag-engine",
        description="Lightweight hybrid RAG engine for multilingual document search",
        version=settings.app_version,
        lifespan=lifespan,
    )

    # Rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router, prefix="/api/v1")
    app.include_router(documents_router, prefix="/api/v1")
    app.include_router(gdpr_router, prefix="/api/v1")

    return app


app = create_app()
