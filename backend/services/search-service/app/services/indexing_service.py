"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Indexing Service — initializes and configures Meilisearch indexes on startup.
"""

import httpx

from backend.shared.logging.logger import get_logger

logger = get_logger("search-service.indexing")

# Meilisearch index configurations per domain
INDEX_CONFIGS = {
    "notes": {
        "searchableAttributes": ["title", "content_md", "tags"],
        "filterableAttributes": ["user_id", "type", "tags", "created_at"],
        "sortableAttributes": ["created_at"],
    },
    "habits": {
        "searchableAttributes": ["name", "description"],
        "filterableAttributes": ["user_id", "type", "created_at"],
        "sortableAttributes": ["created_at"],
    },
    "learning": {
        "searchableAttributes": ["topic", "notes", "name"],
        "filterableAttributes": ["user_id", "type", "created_at"],
        "sortableAttributes": ["created_at"],
    },
    "records": {
        "searchableAttributes": ["content"],
        "filterableAttributes": ["user_id", "type", "database_id", "created_at"],
        "sortableAttributes": ["created_at"],
    },
    "health": {
        "searchableAttributes": ["food_name", "workout_type", "description"],
        "filterableAttributes": ["user_id", "type", "created_at"],
        "sortableAttributes": ["created_at"],
    },
}

# Ranking rules applied to all indexes (order matters in Meilisearch)
RANKING_RULES = [
    "words",
    "typo",
    "proximity",
    "attribute",
    "sort",
    "exactness",
    "created_at:desc",  # Recent items rank higher
]


class IndexingService:
    """Service for initializing and configuring Meilisearch indexes."""

    def __init__(self, search_url: str, search_api_key: str = ""):
        self.search_url = search_url.rstrip("/")
        self.search_api_key = search_api_key

    async def initialize_indexes(self) -> None:
        """
        Initialize all Meilisearch indexes with proper settings.

        This method:
        1. Creates indexes if they don't exist
        2. Sets filterable, sortable, and searchable attributes
        3. Configures ranking rules for relevance and recency

        Failures are non-fatal — logging warnings rather than raising exceptions.
        """
        logger.info("Initializing Meilisearch indexes...")

        async with httpx.AsyncClient(timeout=30.0) as client:
            for index_name, config in INDEX_CONFIGS.items():
                try:
                    # Create index (idempotent — 202 created or 400 already exists)
                    await self._create_index(client, index_name)

                    # Configure index settings
                    await self._set_index_settings(client, index_name, config)

                    logger.info(f"Index '{index_name}' initialized successfully")
                except Exception as exc:
                    logger.warning(f"Failed to initialize index '{index_name}': {exc}")

        logger.info("Meilisearch index initialization complete")

    async def _create_index(self, client: httpx.AsyncClient, index_name: str) -> None:
        """Create a Meilisearch index (idempotent)."""
        url = f"{self.search_url}/indexes"
        payload = {"uid": index_name, "primaryKey": "id"}
        headers = self._meilisearch_headers()

        response = await client.post(url, json=payload, headers=headers)

        # 202 = created, 400 with "index_already_exists" = already exists (both OK)
        if response.status_code not in (202, 201):
            if response.status_code == 400:
                body = response.json()
                if body.get("code") == "index_already_exists":
                    return  # Index already exists, which is fine
            raise RuntimeError(
                f"Meilisearch index creation failed: "
                f"{response.status_code} {response.text}"
            )

    async def _set_index_settings(
        self, client: httpx.AsyncClient, index_name: str, config: dict
    ) -> None:
        """Configure index settings (searchable, filterable, sortable attributes)."""
        url = f"{self.search_url}/indexes/{index_name}/settings"

        settings = {
            "searchableAttributes": config["searchableAttributes"],
            "filterableAttributes": config["filterableAttributes"],
            "sortableAttributes": config["sortableAttributes"],
            "rankingRules": RANKING_RULES,
        }

        headers = self._meilisearch_headers()
        response = await client.patch(url, json=settings, headers=headers)

        if response.status_code >= 400:
            raise RuntimeError(
                f"Meilisearch settings update failed: "
                f"{response.status_code} {response.text}"
            )

    def _meilisearch_headers(self) -> dict[str, str]:
        """Build headers for Meilisearch requests."""
        headers = {"Content-Type": "application/json"}
        if self.search_api_key:
            headers["Authorization"] = f"Bearer {self.search_api_key}"
        return headers
