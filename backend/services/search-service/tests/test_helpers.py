"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Shared test helpers and constants for the search service tests.
"""

# Test user IDs
USER_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
OTHER_USER_ID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"


def meili_response(hits: list[dict], total: int | None = None) -> dict:
    """Generate a mock Meilisearch response."""
    return {
        "hits": hits,
        "query": "test",
        "processingTimeMs": 1,
        "estimatedTotalHits": total if total is not None else len(hits),
    }
