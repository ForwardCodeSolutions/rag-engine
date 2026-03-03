"""Tests for the health check endpoint."""

from fastapi.testclient import TestClient

from rag_engine.api.app import app

client = TestClient(app)


class TestHealthEndpoint:
    """Tests for GET /api/v1/health."""

    def test_health_returns_200(self) -> None:
        response = client.get("/api/v1/health")
        assert response.status_code == 200

    def test_health_response_structure(self) -> None:
        data = client.get("/api/v1/health").json()
        assert data["status"] == "healthy"
        assert data["qdrant_connected"] is False
        assert data["version"] == "0.1.0"
