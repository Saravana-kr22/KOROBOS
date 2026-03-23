"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Search Service — queries Meilisearch with caching and user isolation.
"""

import asyncio
import hashlib
import json
import time
from datetime import datetime, timezone
from typing import Any

import httpx
import redis.asyncio as aioredis
from app.schemas.search_schema import SearchQuery, SearchResponse, SuggestResponse

from backend.shared.logging.logger import get_logger

logger = get_logger("search-service")

# Meilisearch index name to type mapping
INDEXES = {
    "notes": "note",
    "records": "record",
    "learning": "learning",
    "habits": "habit",
    "health": ["meal", "workout"],  # health index contains both meal and workout types
}


class SearchService:
    """Service for querying Meilisearch with caching and user isolation."""

    def __init__(
        self, redis_client: aioredis.Redis, search_url: str, search_api_key: str = ""
    ):
        self.redis = redis_client
        self.search_url = search_url.rstrip("/")
        self.search_api_key = search_api_key

    def _build_filter(self, user_id: str, query: SearchQuery | None = None) -> str:
        """Build compound Meilisearch filter expression with user isolation."""
        filters = [f"user_id = '{user_id}'"]

        if query:
            # Date range filters (stored as Unix timestamps in Meilisearch)
            if query.date_from:
                ts = int(query.date_from.timestamp())
                filters.append(f"created_at >= {ts}")
            if query.date_to:
                ts = int(query.date_to.timestamp())
                filters.append(f"created_at <= {ts}")

            # Tags filter (for notes)
            if query.tags and query.tags:
                tag_list = ", ".join(f'"{t}"' for t in query.tags)
                filters.append(f"tags IN [{tag_list}]")

        return " AND ".join(filters)

    async def search(
        self, query: SearchQuery, user_id: str
    ) -> tuple[SearchResponse, int]:
        """
        Execute a unified search across all relevant indexes.

        Returns:
            (SearchResponse, processing_time_ms)
        """
        start_time = time.time()

        # Check Redis cache
        cache_key = self._cache_key("search", user_id, query)
        cached = await self.redis.get(cache_key)
        if cached:
            logger.debug(f"Search cache hit for user {user_id}")
            result = SearchResponse.model_validate_json(cached)
            elapsed_ms = int((time.time() - start_time) * 1000)
            return result, elapsed_ms

        # Determine which indexes to query
        indexes_to_query = self._indexes_for_query(query)

        # Query each index
        all_results = []
        for index_name in indexes_to_query:
            try:
                results = await self._query_index(index_name, query, user_id)
                all_results.extend(results)
            except Exception as exc:
                logger.error(f"Error querying {index_name}: {exc}")

        # Sort by score (higher first), then by created_at (newer first)
        all_results.sort(
            key=lambda r: (r.score or 0, r.created_at or datetime.min),
            reverse=True,
        )

        # Apply pagination
        total = len(all_results)
        paginated = all_results[query.offset : query.offset + query.limit]

        elapsed_ms = int((time.time() - start_time) * 1000)

        response = SearchResponse(
            query=query.q,
            results=paginated,
            total=total,
            limit=query.limit,
            offset=query.offset,
            processing_time_ms=elapsed_ms,
        )

        # Cache result for 120 seconds
        await self.redis.setex(
            cache_key,
            120,
            response.model_dump_json(),
        )

        return response, elapsed_ms

    async def suggest(self, q: str, user_id: str) -> tuple[SuggestResponse, int]:
        """
        Return autocomplete suggestions from multiple indexes (notes, habits, learning).

        Queries are run in parallel to provide unified suggestions across all domains.

        Returns:
            (SuggestResponse, processing_time_ms)
        """
        start_time = time.time()

        # Check Redis cache
        cache_key = self._cache_key("suggest", user_id, q)
        cached = await self.redis.get(cache_key)
        if cached:
            logger.debug(f"Suggest cache hit for user {user_id}")
            result = SuggestResponse.model_validate_json(cached)
            elapsed_ms = int((time.time() - start_time) * 1000)
            return result, elapsed_ms

        # Query multiple indexes in parallel
        tasks = [
            self._suggest_from_notes(q, user_id),
            self._suggest_from_habits(q, user_id),
            self._suggest_from_learning(q, user_id),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_suggestions = []
        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"Suggest query error: {result}")
                continue
            if isinstance(result, list):
                all_suggestions.extend(result)

        # Deduplicate (case-insensitive) and truncate to 5
        seen = set()
        suggestions = []
        for sugg in all_suggestions:
            sugg_lower = sugg.lower()
            if sugg_lower not in seen and sugg.strip():
                seen.add(sugg_lower)
                suggestions.append(sugg)
                if len(suggestions) >= 5:
                    break

        elapsed_ms = int((time.time() - start_time) * 1000)

        result = SuggestResponse(
            query=q,
            suggestions=suggestions,
        )

        # Cache for 120 seconds
        await self.redis.setex(
            cache_key,
            120,
            result.model_dump_json(),
        )

        return result, elapsed_ms

    async def _suggest_from_notes(self, q: str, user_id: str) -> list[str]:
        """Query notes index for title suggestions."""
        try:
            index_url = f"{self.search_url}/indexes/notes/search"
            payload = {
                "q": q,
                "limit": 5,
                "attributesToSearchOn": ["title"],
                "attributesToRetrieve": ["title"],
                "filter": self._build_filter(user_id),
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    index_url,
                    json=payload,
                    headers=self._meilisearch_headers(),
                )

                if response.status_code == 200:
                    data = response.json()
                    return [hit.get("title", "") for hit in data.get("hits", [])]
        except Exception as exc:
            logger.debug(f"Error querying notes for suggestions: {exc}")

        return []

    async def _suggest_from_habits(self, q: str, user_id: str) -> list[str]:
        """Query habits index for name suggestions."""
        try:
            index_url = f"{self.search_url}/indexes/habits/search"
            payload = {
                "q": q,
                "limit": 5,
                "attributesToSearchOn": ["name"],
                "attributesToRetrieve": ["name"],
                "filter": self._build_filter(user_id),
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    index_url,
                    json=payload,
                    headers=self._meilisearch_headers(),
                )

                if response.status_code == 200:
                    data = response.json()
                    return [hit.get("name", "") for hit in data.get("hits", [])]
        except Exception as exc:
            logger.debug(f"Error querying habits for suggestions: {exc}")

        return []

    async def _suggest_from_learning(self, q: str, user_id: str) -> list[str]:
        """Query learning index for topic/session suggestions."""
        try:
            index_url = f"{self.search_url}/indexes/learning/search"
            payload = {
                "q": q,
                "limit": 5,
                "attributesToSearchOn": ["topic", "name"],
                "attributesToRetrieve": ["topic", "name", "type"],
                "filter": self._build_filter(user_id),
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    index_url,
                    json=payload,
                    headers=self._meilisearch_headers(),
                )

                if response.status_code == 200:
                    data = response.json()
                    suggestions = []
                    for hit in data.get("hits", []):
                        # For topics, use "name"; for sessions, use "topic"
                        if hit.get("type") == "topic":
                            suggestions.append(hit.get("name", ""))
                        else:
                            suggestions.append(hit.get("topic", ""))
                    return suggestions
        except Exception as exc:
            logger.debug(f"Error querying learning for suggestions: {exc}")

        return []

    async def _query_index(
        self, index_name: str, query: SearchQuery, user_id: str
    ) -> list:
        """Query a single Meilisearch index and return normalized results."""
        index_url = f"{self.search_url}/indexes/{index_name}/search"

        # Build Meilisearch query
        payload = {
            "q": query.q,
            "limit": max(
                50, query.limit + query.offset
            ),  # Fetch buffer to reduce cross-index ranking gaps
            "offset": 0,
            "attributesToHighlight": ["*"],
            "filter": self._build_filter(user_id, query),
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    index_url,
                    json=payload,
                    headers=self._meilisearch_headers(),
                )

                if response.status_code != 200:
                    logger.warning(f"Meilisearch query failed: {response.status_code}")
                    return []

                data = response.json()
                results = []

                for hit in data.get("hits", []):
                    # Normalize hit into SearchResult
                    result_type = self._type_from_index(index_name, hit)

                    # Extract snippet from highlight or use default fields
                    snippet = self._extract_snippet(index_name, hit)

                    # Parse created_at (Unix timestamp or ISO string)
                    created_at = None
                    if "created_at" in hit:
                        try:
                            val = hit["created_at"]
                            if isinstance(val, (int, float)):
                                created_at = datetime.fromtimestamp(
                                    val, tz=timezone.utc
                                )
                            else:
                                created_at = datetime.fromisoformat(str(val))
                        except (ValueError, TypeError):
                            pass

                    from app.schemas.search_schema import SearchResult

                    result = SearchResult(
                        id=hit.get("id", ""),
                        type=result_type,
                        title=self._extract_title(index_name, hit),
                        snippet=snippet,
                        user_id=hit.get("user_id", user_id),
                        score=hit.get("_rankingScore"),
                        created_at=created_at,
                    )
                    results.append(result)

                return results

        except Exception as exc:
            logger.error(f"Error querying {index_name}: {exc}")
            return []

    def _indexes_for_query(self, query: SearchQuery) -> list[str]:
        """Determine which indexes to query based on type filter."""
        if not query.type:
            # Query all indexes
            return list(INDEXES.keys())

        # Find index(es) that contain this type
        for index_name, types in INDEXES.items():
            if isinstance(types, list):
                if query.type in types:
                    return [index_name]
            else:
                if query.type == types:
                    return [index_name]

        # Unknown type, query all indexes
        return list(INDEXES.keys())

    def _type_from_index(self, index_name: str, hit: dict[str, Any]) -> str:
        """Extract the result type from an index."""
        # Some indexes explicitly include 'type' field in documents
        if "type" in hit:
            return hit["type"]

        # Fallback to mapping
        types = INDEXES.get(index_name, "unknown")
        if isinstance(types, list):
            return types[0]  # Default to first type if ambiguous
        return types

    def _extract_title(self, index_name: str, hit: dict[str, Any]) -> str:
        """Extract a title/name from a hit based on index."""
        if index_name == "notes":
            return hit.get("title", "Untitled Note")
        elif index_name == "records":
            return f"Record {hit.get('id', '')[:8]}"
        elif index_name == "learning":
            if hit.get("type") == "topic":
                return hit.get("name", "Unknown Topic")
            else:
                return f"{hit.get('topic', 'Learning Session')}"
        elif index_name == "habits":
            return hit.get("name", "Habit")
        elif index_name == "health":
            if hit.get("type") == "meal":
                return hit.get("food_name", "Meal")
            else:
                return hit.get("workout_type", "Workout")
        return "Unknown"

    def _extract_snippet(self, index_name: str, hit: dict[str, Any]) -> str:
        """Extract a snippet/preview from a hit."""
        # Try to use highlighted text first
        if "_formatted" in hit:
            formatted = hit["_formatted"]
            if index_name == "notes":
                content = formatted.get("content_md", "")
                return self._truncate(content, 150)
            elif index_name == "learning":
                notes = formatted.get("notes", "")
                return self._truncate(notes, 150)
            elif index_name == "records":
                content = formatted.get("content", "")
                return self._truncate(content, 150)
            elif index_name == "habits":
                desc = formatted.get("description", "")
                return self._truncate(desc, 150) or f"Frequency: {hit.get('frequency')}"
            elif index_name == "health":
                desc = formatted.get("description", "")
                snippet = self._truncate(desc, 100) if desc else ""
                if hit.get("type") == "meal":
                    calories = hit.get("calories", 0)
                    snippet = (
                        f"{snippet} ({calories} kcal)"
                        if snippet
                        else f"{calories} kcal"
                    )
                else:
                    duration = hit.get("duration", 0)
                    snippet = (
                        f"{snippet} ({duration}min)"
                        if snippet
                        else f"{duration}min workout"
                    )
                return snippet

        # Fallback to raw fields
        if index_name == "notes":
            content = hit.get("content_md", "")
            return self._truncate(content, 150)
        elif index_name == "learning":
            notes = hit.get("notes", "")
            return self._truncate(notes, 150)
        elif index_name == "records":
            content = hit.get("content", "")
            return self._truncate(content, 150)
        elif index_name == "habits":
            return hit.get("description", f"Frequency: {hit.get('frequency')}")
        elif index_name == "health":
            if hit.get("type") == "meal":
                return f"{hit.get('calories', 0)} kcal"
            else:
                return (
                    f"{hit.get('duration', 0)}min {hit.get('workout_type', 'workout')}"
                )

        return ""

    def _truncate(self, text: str, max_length: int = 150) -> str:
        """Truncate text to max_length characters, breaking at word boundary."""
        if len(text) <= max_length:
            return text
        truncated = text[:max_length]
        last_space = truncated.rfind(" ")
        if last_space > max_length - 50:  # Only break at word if close enough
            return truncated[:last_space] + "..."
        return truncated + "..."

    def _cache_key(self, prefix: str, user_id: str, query: Any) -> str:
        """Generate a Redis cache key for a query."""
        if isinstance(query, str):
            query_hash = hashlib.md5(query.encode(), usedforsecurity=False).hexdigest()[
                :8
            ]
        else:
            query_str = json.dumps(query.model_dump(mode="json"), sort_keys=True)
            query_hash = hashlib.md5(
                query_str.encode(), usedforsecurity=False
            ).hexdigest()[:8]
        return f"{prefix}:{user_id}:{query_hash}"

    def _meilisearch_headers(self) -> dict[str, str]:
        """Build headers for Meilisearch requests."""
        headers = {"Content-Type": "application/json"}
        if self.search_api_key:
            headers["Authorization"] = f"Bearer {self.search_api_key}"
        return headers
