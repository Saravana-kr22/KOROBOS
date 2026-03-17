"""
Unit tests for the API Gateway middleware and routing.

Tests: auth middleware (skip public paths, reject missing token, accept valid token),
       gateway routing and health endpoints.
"""

import importlib
import sys
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

# Ensure gateway app is in sys.path
_test_dir = Path(__file__).resolve().parent
_backend_root = _test_dir.parent
_gateway_path = str(_backend_root / "gateway" / "api-gateway")
if _gateway_path not in sys.path:
    sys.path.insert(0, _gateway_path)

# Import the gateway app using importlib to avoid namespace collision
_app_module = importlib.import_module("app.main")
app = _app_module.app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_health_endpoint():
    """Health endpoint should return healthy status without auth."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "api-gateway"


@pytest.mark.anyio
async def test_metrics_endpoint():
    """Metrics endpoint should return service info without auth."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "registered_services" in data["data"]


@pytest.mark.anyio
async def test_docs_accessible():
    """OpenAPI docs should be accessible without auth."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/openapi.json")
        assert response.status_code == 200


@pytest.mark.anyio
async def test_missing_token_on_protected_route():
    """Protected routes should reject requests without Bearer token."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/notes/")
        assert response.status_code == 401
        data = response.json()
        assert data["error"]["code"] == "MISSING_TOKEN"


@pytest.mark.anyio
async def test_invalid_token_on_protected_route():
    """Protected routes should reject invalid tokens."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/v1/notes/",
            headers={"Authorization": "Bearer invalid.jwt.token"},
        )
        assert response.status_code == 401
        data = response.json()
        assert data["error"]["code"] == "INVALID_TOKEN"


@pytest.mark.anyio
async def test_valid_token_on_protected_route():
    """
    Protected routes should accept valid JWT tokens.

    Upstream may fail but auth passes.
    """
    from backend.shared.auth.jwt_handler import create_access_token

    token = create_access_token(
        user_id="test-user-id", email="test@example.com", roles=["user"]
    )

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/v1/notes/",
            headers={"Authorization": f"Bearer {token}"},
        )
        # Should NOT be 401 — auth passed; may be 502 (upstream not running) or 200
        assert response.status_code != 401


@pytest.mark.anyio
async def test_auth_routes_skip_auth():
    """Auth login/signup routes should not require authentication."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # These should NOT return 401 — auth is skipped for these paths
        response = await client.post("/api/v1/auth/login")
        assert response.status_code != 401

        response = await client.post("/api/v1/auth/signup")
        assert response.status_code != 401


@pytest.mark.anyio
async def test_unknown_service_returns_404():
    """Requests to unregistered services should return 404."""
    from backend.shared.auth.jwt_handler import create_access_token

    token = create_access_token(user_id="test-user-id", email="test@example.com")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/v1/nonexistent/resource",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "SERVICE_NOT_FOUND"


@pytest.mark.anyio
async def test_request_id_header():
    """Responses should include X-Request-ID header."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")
        assert "x-request-id" in response.headers
