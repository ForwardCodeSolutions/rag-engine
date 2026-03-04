"""Tests for API authentication."""

from fastapi.testclient import TestClient

from rag_engine.api.app import app

client = TestClient(app)
VALID_HEADERS = {"X-API-Key": "test-api-key"}


class TestAuthentication:
    """Tests for X-API-Key authentication."""

    def test_health_no_auth_required(self) -> None:
        response = client.get("/api/v1/health")
        assert response.status_code == 200

    def test_gdpr_delete_without_key_returns_422(self) -> None:
        response = client.delete(
            "/api/v1/documents/doc-1",
            params={"tenant_id": "t1"},
        )
        assert response.status_code == 422

    def test_gdpr_delete_with_wrong_key_returns_401(self) -> None:
        response = client.delete(
            "/api/v1/documents/doc-1",
            params={"tenant_id": "t1"},
            headers={"X-API-Key": "wrong"},
        )
        assert response.status_code == 401

    def test_gdpr_delete_with_valid_key_returns_200(self) -> None:
        response = client.delete(
            "/api/v1/documents/doc-1",
            params={"tenant_id": "t1"},
            headers=VALID_HEADERS,
        )
        assert response.status_code == 200

    def test_search_without_key_returns_422(self) -> None:
        response = client.post(
            "/api/v1/documents/search",
            json={"query": "test", "tenant_id": "t1"},
        )
        assert response.status_code == 422

    def test_search_with_valid_key_returns_200(self) -> None:
        response = client.post(
            "/api/v1/documents/search",
            json={"query": "test", "tenant_id": "t1"},
            headers=VALID_HEADERS,
        )
        assert response.status_code == 200

    def test_upload_without_key_returns_422(self) -> None:
        response = client.post(
            "/api/v1/documents/upload",
            data={"tenant_id": "t1"},
            files={"file": ("test.txt", b"content", "text/plain")},
        )
        assert response.status_code == 422

    def test_upload_with_valid_key_returns_200(self) -> None:
        response = client.post(
            "/api/v1/documents/upload",
            data={"tenant_id": "t1"},
            files={"file": ("test.txt", b"Some test content here", "text/plain")},
            headers=VALID_HEADERS,
        )
        assert response.status_code == 200
