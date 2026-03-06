"""Integration tests for API rate limiting (429 on excess requests)."""

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address


class TestAPIRateLimiting:
    """Verify rate limiter returns 429 when limits are exceeded."""

    _headers = {"X-API-Key": "test-api-key"}

    def _create_limited_app(self, limit: str = "2/minute") -> FastAPI:
        """Create a minimal app with a tight rate limit for testing."""
        limiter = Limiter(key_func=get_remote_address)
        app = FastAPI()
        app.state.limiter = limiter
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

        @app.get("/limited")
        @limiter.limit(limit)
        async def limited_endpoint(request: Request) -> dict:
            return {"ok": True}

        @app.get("/unlimited")
        async def unlimited_endpoint() -> dict:
            return {"ok": True}

        return app

    def test_rate_limit_returns_429_after_exceeding(self) -> None:
        """Exhaust the rate limit and verify 429 response."""
        app = self._create_limited_app("3/minute")
        client = TestClient(app)

        # First 3 requests should succeed
        for _ in range(3):
            resp = client.get("/limited")
            assert resp.status_code == 200

        # 4th request should be rate limited
        resp = client.get("/limited")
        assert resp.status_code == 429

    def test_unlimited_endpoint_always_responds_200(self) -> None:
        """Endpoint without rate limit should always respond 200."""
        app = self._create_limited_app("2/minute")
        client = TestClient(app)

        for _ in range(20):
            resp = client.get("/unlimited")
            assert resp.status_code == 200

    def test_health_endpoint_not_rate_limited(self) -> None:
        """Health endpoint on the real app should always respond 200."""
        from rag_engine.api.app import create_app

        client = TestClient(create_app())
        for _ in range(20):
            resp = client.get("/api/v1/health")
            assert resp.status_code == 200
