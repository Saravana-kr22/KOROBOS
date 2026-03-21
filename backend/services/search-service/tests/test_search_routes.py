"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Integration tests for Search Service API endpoints.
"""

from unittest.mock import AsyncMock, patch

import pytest

from .test_helpers import USER_ID, meili_response

# -- GET /search --


@pytest.mark.asyncio
async def test_search_missing_q_returns_422(client):
    """Missing required 'q' parameter returns 422."""
    resp = await client.get("/search", headers={"X-User-ID": USER_ID})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_search_missing_user_id_returns_422(client):
    """Missing X-User-ID header returns 422."""
    resp = await client.get("/search?q=test")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_search_returns_200_with_results(client):
    """Successful search returns 200 with results."""
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = meili_response(
            [
                {
                    "id": "note-1",
                    "title": "Test Note",
                    "content_md": "Testing search",
                    "user_id": USER_ID,
                    "type": "note",
                    "_rankingScore": 0.95,
                    "created_at": "2026-03-22T00:00:00",
                },
                {
                    "id": "habit-1",
                    "name": "Test Habit",
                    "user_id": USER_ID,
                    "type": "habit",
                    "_rankingScore": 0.85,
                    "created_at": "2026-03-22T00:00:00",
                },
            ]
        )
        mock_post.return_value = mock_response

        resp = await client.get(
            "/search?q=test",
            headers={"X-User-ID": USER_ID},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["query"] == "test"
        assert len(body["results"]) == 2
        assert body["results"][0]["type"] in ("note", "habit")


@pytest.mark.asyncio
async def test_search_with_type_filter(client):
    """Type filter restricts search to specific index."""
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = meili_response([])
        mock_post.return_value = mock_response

        resp = await client.get(
            "/search?q=test&type=habit",
            headers={"X-User-ID": USER_ID},
        )

        assert resp.status_code == 200
        # Verify only the habits index was queried
        assert mock_post.call_count == 1
        call_url = mock_post.call_args[0][0]
        assert "habits" in call_url


@pytest.mark.asyncio
async def test_search_limit_above_50_returns_422(client):
    """Limit > 50 is rejected."""
    resp = await client.get(
        "/search?q=test&limit=51",
        headers={"X-User-ID": USER_ID},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_search_user_isolation(client):
    """Search query includes user_id filter."""
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = meili_response([])
        mock_post.return_value = mock_response

        resp = await client.get(
            "/search?q=test",
            headers={"X-User-ID": USER_ID},
        )

        assert resp.status_code == 200
        # Verify user_id filter is in request
        call_args = mock_post.call_args
        request_body = call_args.kwargs["json"]
        assert f"user_id = '{USER_ID}'" in request_body.get("filter", "")


@pytest.mark.asyncio
async def test_search_rate_limit_exceeded(client):
    """Rate limit 429 when over limit."""
    client.app.state.redis.get.return_value = None  # Cache miss
    client.app.state.redis.incr.return_value = 201  # Over the limit
    client.app.state.redis.expire = AsyncMock()

    resp = await client.get(
        "/search?q=test",
        headers={"X-User-ID": USER_ID},
    )

    assert resp.status_code == 429
    body = resp.json()
    assert body["error"]["code"] == "RATE_LIMIT_EXCEEDED"


# -- GET /search/advanced --


@pytest.mark.asyncio
async def test_advanced_search_with_date_filters(client):
    """Advanced search with date range filters."""
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = meili_response([])
        mock_post.return_value = mock_response

        resp = await client.get(
            "/search/advanced?q=test&date_from=2026-01-01&date_to=2026-12-31",
            headers={"X-User-ID": USER_ID},
        )

        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_advanced_search_with_tags(client):
    """Advanced search with tags filter."""
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = meili_response([])
        mock_post.return_value = mock_response

        resp = await client.get(
            "/search/advanced?q=test&tags=python,ai",
            headers={"X-User-ID": USER_ID},
        )

        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_advanced_search_missing_q_returns_422(client):
    """Advanced search without 'q' returns 422."""
    resp = await client.get(
        "/search/advanced",
        headers={"X-User-ID": USER_ID},
    )
    assert resp.status_code == 422


# -- GET /search/suggest --


@pytest.mark.asyncio
async def test_suggest_returns_suggestions(client):
    """Suggest endpoint returns autocomplete suggestions."""
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = AsyncMock()
        mock_response.status_code = 200

        # Mock 3 indexes returning different suggestions
        mock_post.side_effect = [
            # notes index
            type(
                "Response",
                (),
                {
                    "status_code": 200,
                    "json": lambda: meili_response(
                        [
                            {"title": "Machine Learning"},
                            {"title": "Machine Vision"},
                        ]
                    ),
                },
            )(),
            # habits index
            type(
                "Response",
                (),
                {
                    "status_code": 200,
                    "json": lambda: meili_response([]),
                },
            )(),
            # learning index
            type(
                "Response",
                (),
                {
                    "status_code": 200,
                    "json": lambda: meili_response([]),
                },
            )(),
        ]

        resp = await client.get(
            "/search/suggest?q=mach",
            headers={"X-User-ID": USER_ID},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body["suggestions"], list)
        assert len(body["suggestions"]) <= 5


@pytest.mark.asyncio
async def test_suggest_missing_q_returns_422(client):
    """Suggest without 'q' returns 422."""
    resp = await client.get(
        "/search/suggest",
        headers={"X-User-ID": USER_ID},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_suggest_deduplicates(client):
    """Suggest deduplicates suggestions from multiple indexes."""
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.side_effect = [
            # notes: returns "Machine Learning"
            type(
                "Response",
                (),
                {
                    "status_code": 200,
                    "json": lambda: meili_response([{"title": "Machine Learning"}]),
                },
            )(),
            # habits: returns "Machine Learning" (different case)
            type(
                "Response",
                (),
                {
                    "status_code": 200,
                    "json": lambda: meili_response([{"name": "machine learning"}]),
                },
            )(),
            # learning: returns nothing
            type(
                "Response",
                (),
                {
                    "status_code": 200,
                    "json": lambda: meili_response([]),
                },
            )(),
        ]

        resp = await client.get(
            "/search/suggest?q=mach",
            headers={"X-User-ID": USER_ID},
        )

        assert resp.status_code == 200
        body = resp.json()
        # Should not have duplicates
        assert len(body["suggestions"]) == 1
        assert body["suggestions"][0].lower() == "machine learning"
