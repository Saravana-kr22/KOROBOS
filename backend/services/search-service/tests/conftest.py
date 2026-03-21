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

from .test_helpers import USER_ID


@pytest_asyncio.fixture
async def client():
    """
    AsyncClient with ASGITransport for testing the search-service.

    Mocks Redis and Meilisearch to avoid external dependencies.
    """
    # Mock Redis
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None  # Cache miss by default
    app.state.redis = mock_redis

    # Mock search configuration
    app.state.search_url = "http://meilisearch:7700"
    app.state.search_api_key = "test-key"

    # Mock index initialization (patch the indexing service call in lifespan)
    with patch(
        "app.services.indexing_service.IndexingService.initialize_indexes",
        new_callable=AsyncMock,
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            yield ac


@pytest.fixture
def headers(user_id: str = USER_ID) -> dict:
    """Generate request headers with X-User-ID."""
    return {"X-User-ID": user_id}
