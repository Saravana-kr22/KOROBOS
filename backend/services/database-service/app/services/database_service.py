"""
KOROBOS — Database Service Business Logic

High-level operations for database management.
"""

import logging
import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.database_service.app.models.database_model import Database
from backend.services.database_service.app.models.property_model import Property
from backend.services.database_service.app.repositories.database_repository import (
    DatabaseRepository,
)
from backend.services.database_service.app.repositories.property_repository import (
    PropertyRepository,
)
from backend.services.database_service.app.schemas.database_schema import (
    DatabaseCreate,
    DatabaseUpdate,
    PropertyCreate,
)
from backend.shared.messaging.producer import publish_event

logger = logging.getLogger(__name__)


class DatabaseService:
    """Service for database operations."""

    def __init__(self, session: AsyncSession, redis=None):
        self.session = session
        self.repo = DatabaseRepository(session)
        self.prop_repo = PropertyRepository(session)
        self.redis = redis

    async def create_database(
        self,
        user_id: uuid.UUID,
        data: DatabaseCreate,
    ) -> Database:
        """Create a new database.

        Publishes a database.created event to Kafka.

        Args:
            user_id: User creating the database
            data: Database creation data

        Returns:
            Created Database instance
        """
        db = await self.repo.create(
            user_id=user_id,
            name=data.name,
            icon=data.icon,
            description=data.description,
        )

        # Publish event
        from backend.services.database_service.app.events.database_events import (
            DatabaseCreatedEvent,
        )

        event = DatabaseCreatedEvent(
            payload={
                "database_id": str(db.id),
                "user_id": str(user_id),
                "name": db.name,
            }
        )
        try:
            await publish_event(event, key=str(user_id))
        except Exception as e:
            logger.warning(f"Failed to publish database.created event: {e}")

        # Invalidate cache
        await self._invalidate_db_cache(user_id)

        return db

    async def get_database(
        self,
        db_id: uuid.UUID,
    ) -> Optional[Database]:
        """Fetch a database by ID.

        Args:
            db_id: Database ID

        Returns:
            Database instance or None if not found
        """
        return await self.repo.get_by_id(db_id)

    async def list_databases(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[Database], int]:
        """List databases for a user with pagination.

        Checks Redis cache first (5-minute TTL). Cache includes only
        basic metadata (id, name, icon) not nested properties.

        Args:
            user_id: User ID
            page: Page number (1-indexed)
            limit: Results per page

        Returns:
            Tuple of (databases, total_count)
        """
        import json

        offset = (page - 1) * limit
        cache_key = f"db:user:{user_id}:page:{page}:{limit}"

        # Try Redis cache if available
        if self.redis:
            try:
                cached = await self.redis.get(cache_key)
                if cached:
                    data = json.loads(cached)
                    logger.debug(f"Cache hit for {cache_key}")

                    # Reconstruct Database objects from cached data
                    # Note: properties are excluded from cache (lazy-loaded)
                    cached_databases = []
                    for db_data in data.get("databases", []):
                        db = Database(
                            id=uuid.UUID(db_data["id"]),
                            user_id=user_id,
                            name=db_data["name"],
                            icon=db_data.get("icon"),
                            description=db_data.get("description"),
                            created_at=db_data["created_at"],
                            updated_at=db_data["updated_at"],
                        )
                        # Attach empty properties list (will be lazy-loaded if needed)
                        db.properties = []
                        cached_databases.append(db)

                    return cached_databases, data["total"]
            except Exception as e:
                logger.warning(f"Redis cache read failed: {e}")
                # Fall through to DB query on cache error

        # Cache miss or redis unavailable - fetch from database
        databases, total = await self.repo.list_by_user(
            user_id, offset=offset, limit=limit
        )

        # Update cache with fetched data
        if self.redis and databases:
            try:
                cache_data = {
                    "databases": [
                        {
                            "id": str(db.id),
                            "name": db.name,
                            "icon": db.icon,
                            "description": db.description,
                            "created_at": db.created_at.isoformat(),
                            "updated_at": db.updated_at.isoformat(),
                        }
                        for db in databases
                    ],
                    "total": total,
                }
                await self.redis.set(
                    cache_key, json.dumps(cache_data), ex=300
                )  # 5 minute TTL
                logger.debug(f"Cache set for {cache_key} ({len(databases)} items)")
            except Exception as e:
                logger.warning(f"Redis cache write failed: {e}")
                # Graceful degradation - return data even if cache fails

        return databases, total

    async def update_database(
        self,
        db: Database,
        data: DatabaseUpdate,
    ) -> Database:
        """Update a database.

        Args:
            db: Database instance to update
            data: Update data

        Returns:
            Updated Database instance
        """
        updated = await self.repo.update(
            db,
            name=data.name,
            icon=data.icon,
            description=data.description,
        )

        # Invalidate cache
        await self._invalidate_db_cache(db.user_id)

        return updated

    async def delete_database(
        self,
        db: Database,
    ) -> None:
        """Delete a database.

        Args:
            db: Database instance to delete
        """
        user_id = db.user_id
        await self.repo.delete(db)

        # Invalidate cache
        await self._invalidate_db_cache(user_id)

    async def add_property(
        self,
        database_id: uuid.UUID,
        data: PropertyCreate,
    ) -> Property:
        """Add a property to a database.

        Args:
            database_id: Database ID
            data: Property creation data

        Returns:
            Created Property instance
        """
        prop = await self.prop_repo.create(
            database_id=database_id,
            name=data.name,
            type=data.type,
            options=data.options,
            position=data.position,
        )

        # Invalidate cache (depends on database lookup)
        # Could also invalidate specific database cache

        return prop

    async def delete_property(
        self,
        prop: Property,
    ) -> None:
        """Delete a property.

        Args:
            prop: Property instance to delete
        """
        await self.prop_repo.delete(prop)

    async def _invalidate_db_cache(
        self,
        user_id: uuid.UUID,
    ) -> None:
        """Invalidate all cached database lists for a user.

        Uses wildcard pattern to delete all cached pages.

        Args:
            user_id: User ID
        """
        if not self.redis:
            return

        try:
            pattern = f"db:user:{user_id}:*"
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)
                logger.debug(f"Invalidated {len(keys)} cache keys for user {user_id}")
        except Exception as e:
            logger.warning(f"Redis cache invalidation failed: {e}")
