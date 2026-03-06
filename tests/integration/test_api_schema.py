"""API schema validation tests using Schemathesis."""

import schemathesis
from slowapi import Limiter
from slowapi.util import get_remote_address
from schemathesis.openapi import from_asgi

from rag_engine.api.app import create_app
from rag_engine.api.routes import rate_limit

# Create a dedicated app with a fresh rate limiter to avoid polluting other tests
_original_limiter = rate_limit.limiter
rate_limit.limiter = Limiter(key_func=get_remote_address)
_schema_app = create_app()
rate_limit.limiter = _original_limiter

schema = from_asgi("/openapi.json", app=_schema_app)


@schema.parametrize()
def test_api_schema_conformance(case) -> None:
    """All API responses must conform to the OpenAPI schema (no 5xx errors)."""
    case.headers = {"X-API-Key": "test-api-key"}
    response = case.call(app=_schema_app)
    case.validate_response(response, checks=[schemathesis.checks.not_a_server_error])
