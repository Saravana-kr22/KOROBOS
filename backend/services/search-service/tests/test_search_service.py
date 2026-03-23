"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Unit tests for SearchService and IndexingService.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.schemas.search_schema import SearchQuery
from app.services.indexing_service import IndexingService
from app.services.search_service import SearchService

from .helpers import USER_ID, meili_response

# -- SearchService.search() --


@pytest.mark.asyncio
async def test_search_returns_cache_hit():
    """Search returns cached result without querying Meilisearch."""
    mock_redis = AsyncMock()
    cached_response = (
        '{"query":"test","results":[],"total":0,"limit":20,'
        '"offset":0,"processing_time_ms":1}'
    )
    mock_redis.get.return_value = cached_response

    service = SearchService(mock_redis, "http://meilisearch:7700", "key")
    query = SearchQuery(q="test")

    result, elapsed = await service.search(query, USER_ID)

    assert result.query == "test"
    assert result.total == 0
    # Verify Redis get was called
    assert mock_redis.get.called


@pytest.mark.asyncio
async def test_search_caches_result():
    """Search caches result in Redis after query."""
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None  # Cache miss

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = meili_response([])
        mock_post.return_value = mock_response

        service = SearchService(mock_redis, "http://meilisearch:7700", "key")
        query = SearchQuery(q="test")

        result, _ = await service.search(query, USER_ID)

        # Verify Redis setex was called (caching)
        assert mock_redis.setex.called
        call_args = mock_redis.setex.call_args
        assert call_args[0][1] == 120  # TTL is 120 seconds


@pytest.mark.asyncio
async def test_search_merges_multiple_indexes():
    """Search merges results from multiple indexes."""
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        # Mock multiple index responses
        notes_response = MagicMock()
        notes_response.status_code = 200
        notes_response.json.return_value = meili_response(
            [{"id": "1", "title": "Note 1", "type": "note", "_rankingScore": 0.9}]
        )

        habits_response = MagicMock()
        habits_response.status_code = 200
        habits_response.json.return_value = meili_response(
            [{"id": "2", "name": "Habit 1", "type": "habit", "_rankingScore": 0.8}]
        )

        mock_post.side_effect = [
            notes_response,
            habits_response,
            habits_response,
            habits_response,
            habits_response,
        ]

        service = SearchService(mock_redis, "http://meilisearch:7700", "key")
        query = SearchQuery(q="test")

        result, _ = await service.search(query, USER_ID)

        # Both indexes should be queried, results merged
        assert mock_post.call_count >= 2


@pytest.mark.asyncio
async def test_search_handles_meilisearch_error_gracefully():
    """Search handles Meilisearch errors without failing."""
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        error_response = MagicMock()
        error_response.status_code = 500

        ok_response = MagicMock()
        ok_response.status_code = 200
        ok_response.json.return_value = meili_response(
            [{"id": "1", "title": "Habit 1", "type": "habit", "_rankingScore": 0.9}]
        )

        # First index fails, others succeed
        mock_post.side_effect = [
            error_response,
            ok_response,
            ok_response,
            ok_response,
            ok_response,
        ]

        service = SearchService(mock_redis, "http://meilisearch:7700", "key")
        query = SearchQuery(q="test")

        result, _ = await service.search(query, USER_ID)

        # Should still return results from successful indexes
        assert result.total >= 0


# -- SearchService.suggest() --


@pytest.mark.asyncio
async def test_suggest_queries_multiple_indexes_in_parallel():
    """Suggest queries multiple indexes concurrently."""
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = meili_response([])
        mock_post.return_value = mock_response

        service = SearchService(mock_redis, "http://meilisearch:7700", "key")

        result, _ = await service.suggest("test", USER_ID)

        # Should query 3 indexes: notes, habits, learning
        assert mock_post.call_count == 3


@pytest.mark.asyncio
async def test_suggest_truncates_to_five():
    """Suggest returns max 5 suggestions."""
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        # Return 7 total suggestions
        notes_response = MagicMock()
        notes_response.status_code = 200
        notes_response.json.return_value = meili_response(
            [{"title": f"Note {i}"} for i in range(5)]
        )

        habits_response = MagicMock()
        habits_response.status_code = 200
        habits_response.json.return_value = meili_response(
            [{"name": f"Habit {i}"} for i in range(2)]
        )

        learning_response = MagicMock()
        learning_response.status_code = 200
        learning_response.json.return_value = meili_response([])

        mock_post.side_effect = [notes_response, habits_response, learning_response]

        service = SearchService(mock_redis, "http://meilisearch:7700", "key")

        result, _ = await service.suggest("test", USER_ID)

        # Should be truncated to 5
        assert len(result.suggestions) <= 5


@pytest.mark.asyncio
async def test_suggest_deduplicates_case_insensitive():
    """Suggest deduplicates suggestions case-insensitively."""
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None

    service = SearchService(mock_redis, "http://meilisearch:7700", "key")

    # Mock the internal suggest methods directly to avoid httpx/asyncio ordering issues
    with (
        patch.object(
            service,
            "_suggest_from_notes",
            new=AsyncMock(return_value=["Machine Learning"]),
        ),
        patch.object(
            service,
            "_suggest_from_habits",
            new=AsyncMock(return_value=["machine learning"]),
        ),
        patch.object(
            service,
            "_suggest_from_learning",
            new=AsyncMock(return_value=[]),
        ),
    ):
        result, _ = await service.suggest("mach", USER_ID)

    # Should have only 1 (deduplicated)
    assert len(result.suggestions) == 1


# -- IndexingService.initialize_indexes() --


@pytest.mark.asyncio
async def test_initialize_indexes_calls_settings_for_all_five():
    """IndexingService initializes settings for all 5 indexes."""
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post, patch(
        "httpx.AsyncClient.patch", new_callable=AsyncMock
    ) as mock_patch:
        mock_create_response = MagicMock()
        mock_create_response.status_code = 202
        mock_post.return_value = mock_create_response

        mock_settings_response = MagicMock()
        mock_settings_response.status_code = 200
        mock_patch.return_value = mock_settings_response

        service = IndexingService("http://meilisearch:7700", "key")
        await service.initialize_indexes()

        # Should PATCH settings for all 5 indexes
        patch_calls = [call for call in mock_patch.call_args_list]
        assert len(patch_calls) == 5


@pytest.mark.asyncio
async def test_initialize_indexes_tolerates_meilisearch_unavailable():
    """IndexingService doesn't raise when Meilisearch is unavailable."""
    import httpx

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_instance = AsyncMock()
        mock_instance.__aenter__.return_value = mock_instance

        # Simulate connection error
        mock_instance.post.side_effect = httpx.ConnectError("Connection refused")

        mock_client_class.return_value = mock_instance

        service = IndexingService("http://unreachable:7700", "key")

        # Should not raise exception
        try:
            await service.initialize_indexes()
        except Exception as exc:
            pytest.fail(f"IndexingService raised {type(exc).__name__}: {exc}")
