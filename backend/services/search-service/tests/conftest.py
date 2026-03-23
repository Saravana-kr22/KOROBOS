"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

pytest fixtures for the Search Service test suite.
"""

from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from app.main import app
from httpx import ASGITransport, AsyncClient

from .helpers import USER_ID


@pytest_asyncio.fixture
async def client():
    """
    AsyncClient with ASGITransport for testing the search-service.

    Mocks Redis and Meilisearch to avoid external dependencies.
    """
    # Mock Redis
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None  # Cache miss by default
    mock_redis.ping = AsyncMock(return_value=True)
    mock_redis.aclose = AsyncMock()

    # We assign it initially, but lifespan will overwrite it unless we
    # patch aioredis.from_url
    app.state.redis = mock_redis

    # Mock search configuration
    app.state.search_url = "http://meilisearch:7700"
    app.state.search_api_key = "test-key"

    # Patch lifespan dependencies to avoid real connections
    with (
        patch("app.main.aioredis.from_url", return_value=mock_redis),
        patch(
            "app.services.indexing_service.IndexingService.initialize_indexes",
            new_callable=AsyncMock,
        ),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            ac.app = app
            # Re-ensure app.state.redis is our mock (lifespan should have
            # set it)
            ac.app.state.redis = mock_redis
            yield ac


@pytest.fixture
def headers(user_id: str = USER_ID) -> dict:
    """Generate request headers with X-User-ID."""
    return {"X-User-ID": user_id}
