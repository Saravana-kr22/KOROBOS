"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Search Service Routes — /search, /search/advanced, /search/suggest endpoints.
"""

from datetime import datetime

import redis.asyncio as aioredis
from app.api.rate_limit import RateLimiter
from app.schemas.search_schema import SearchQuery, SearchResponse, SuggestResponse
from app.services.search_service import SearchService
from fastapi import APIRouter, Depends, Header, Query, Request
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/search", tags=["Search"])


async def _get_user_id(x_user_id: str = Header(...)) -> str:
    """Extract user ID from X-User-ID header."""
    return x_user_id


async def _get_redis(request: Request) -> aioredis.Redis:
    """Get Redis client from app state."""
    return request.app.state.redis


@router.get(
    "",
    response_model=SearchResponse,
    summary="Basic unified search",
    description="Search across all domains with keyword and optional type filter",
)
async def search(
    request: Request,
    q: str = Query(..., description="Search query"),
    type: str | None = Query(None, description="Filter by type"),
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    x_user_id: str = Depends(_get_user_id),
) -> SearchResponse:
    """
    Execute a basic search across all indexed domains.

    Query parameters:
    - `q` (required): Search query string
    - `type` (optional): Filter by type (note, habit, learning, record, meal, workout)
    - `limit`: Results per page (default 20, max 50)
    - `offset`: Pagination offset (default 0)

    Returns unified search results ranked by relevance.
    """
    # Rate limiting
    redis_client = request.app.state.redis
    if redis_client:
        rate_limiter = RateLimiter(redis_client)
        if not await rate_limiter.is_allowed(x_user_id, "search", 200):  # 200 req/min
            return JSONResponse(
                status_code=429,
                content={
                    "status": "error",
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many search requests",
                    },
                },
            )

    # Build query
    query = SearchQuery(
        q=q,
        type=type,
        limit=limit,
        offset=offset,
    )

    # Execute search
    search_service = SearchService(
        redis_client,
        request.app.state.search_url,
        request.app.state.search_api_key,
    )

    response, _ = await search_service.search(query, x_user_id)
    return response


@router.get(
    "/advanced",
    response_model=SearchResponse,
    summary="Advanced search with filters",
    description="Search with date range, tags, and type filters",
)
async def search_advanced(
    request: Request,
    q: str = Query(..., description="Search query"),
    type: str | None = Query(None, description="Filter by type"),
    date_from: datetime | None = Query(
        None, description="Filter from date (ISO format)"
    ),
    date_to: datetime | None = Query(None, description="Filter to date (ISO format)"),
    tags: str | None = Query(None, description="Comma-separated tags (notes only)"),
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    x_user_id: str = Depends(_get_user_id),
) -> SearchResponse:
    """
    Execute an advanced search with filters.

    Query parameters:
    - `q` (required): Search query string
    - `type` (optional): Filter by type (note, habit, learning, record, meal, workout)
    - `date_from` (optional): Filter from date (ISO 8601 format)
    - `date_to` (optional): Filter to date (ISO 8601 format)
    - `tags` (optional): Comma-separated tags (notes only)
    - `limit`: Results per page (default 20, max 50)
    - `offset`: Pagination offset (default 0)

    Returns filtered and ranked search results.
    """
    # Rate limiting
    redis_client = request.app.state.redis
    if redis_client:
        rate_limiter = RateLimiter(redis_client)
        if not await rate_limiter.is_allowed(x_user_id, "search", 200):
            return JSONResponse(
                status_code=429,
                content={
                    "status": "error",
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many search requests",
                    },
                },
            )

    # Parse tags
    tag_list = [t.strip() for t in tags.split(",")] if tags else None

    # Build query
    query = SearchQuery(
        q=q,
        type=type,
        date_from=date_from,
        date_to=date_to,
        tags=tag_list,
        limit=limit,
        offset=offset,
    )

    # Execute search
    search_service = SearchService(
        redis_client,
        request.app.state.search_url,
        request.app.state.search_api_key,
    )

    response, _ = await search_service.search(query, x_user_id)
    return response


@router.get(
    "/suggest",
    response_model=SuggestResponse,
    summary="Autocomplete suggestions",
    description="Get search suggestions based on note titles",
)
async def suggest(
    request: Request,
    q: str = Query(..., description="Partial search query for suggestions"),
    x_user_id: str = Depends(_get_user_id),
) -> SuggestResponse:
    """
    Get autocomplete suggestions based on note titles.

    Query parameters:
    - `q` (required): Partial search query

    Returns up to 5 matching note titles as suggestions.
    """
    redis_client = request.app.state.redis

    search_service = SearchService(
        redis_client,
        request.app.state.search_url,
        request.app.state.search_api_key,
    )

    response, _ = await search_service.suggest(q, x_user_id)
    return response
