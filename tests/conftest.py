"""Shared pytest fixtures for rag-engine tests."""

import os

# Set test API key before any app imports (Settings is evaluated at import time)
os.environ.setdefault("API_KEY", "test-api-key")

import pytest
from fastapi.testclient import TestClient
from qdrant_client import QdrantClient

from rag_engine.api.app import create_app
from rag_engine.services.gdpr import GDPRService
from rag_engine.storage.bm25_store import BM25Store
from rag_engine.storage.knowledge_graph import KnowledgeGraphStore
from rag_engine.storage.qdrant_store import QdrantStore

TEST_API_KEY = "test-api-key"


@pytest.fixture
def api_headers() -> dict[str, str]:
    """Headers with valid API key for authenticated requests."""
    return {"X-API-Key": TEST_API_KEY}


@pytest.fixture
def bm25_store() -> BM25Store:
    """Fresh BM25 store for each test."""
    return BM25Store()


@pytest.fixture
def graph_store() -> KnowledgeGraphStore:
    """Fresh Knowledge Graph store for each test."""
    return KnowledgeGraphStore()


@pytest.fixture
def qdrant_client() -> QdrantClient:
    """In-memory Qdrant client for testing."""
    return QdrantClient(":memory:")


@pytest.fixture
def qdrant_store(qdrant_client: QdrantClient) -> QdrantStore:
    """Fresh Qdrant store backed by in-memory client."""
    return QdrantStore(client=qdrant_client)


@pytest.fixture
def gdpr_service(
    bm25_store: BM25Store,
    graph_store: KnowledgeGraphStore,
    qdrant_store: QdrantStore,
) -> GDPRService:
    """GDPR service wired to all test stores."""
    return GDPRService(bm25_store, graph_store, qdrant_store)


@pytest.fixture
def test_client() -> TestClient:
    """FastAPI test client."""
    app = create_app()
    return TestClient(app)
