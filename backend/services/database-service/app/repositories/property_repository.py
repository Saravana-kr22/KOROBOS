"""
KOROBOS — Database Service Property Repository

Data access layer for properties (database fields).
"""

import uuid
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.database_service.app.models.property_model import Property


class PropertyRepository:
    """Repository for property CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        database_id: uuid.UUID,
        name: str,
        type: str,
        options: Optional[dict[str, Any]] = None,
        position: int = 0,
    ) -> Property:
        """Create a new property.

        Args:
            database_id: Parent database ID
            name: Property name
            type: Property type (text, number, boolean, date, select,
                multi_select, relation)
            options: Type-specific config (e.g., select choices)
            position: Column order

        Returns:
            Created Property instance
        """
        prop = Property(
            database_id=database_id,
            name=name,
            type=type,
            options=options,
            position=position,
        )
        self.session.add(prop)
        await self.session.flush()
        return prop

    async def get_by_id(self, prop_id: uuid.UUID) -> Optional[Property]:
        """Fetch a property by ID.

        Args:
            prop_id: Property ID

        Returns:
            Property instance or None if not found
        """
        stmt = select(Property).where(Property.id == prop_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_database(
        self,
        database_id: uuid.UUID,
    ) -> list[Property]:
        """Fetch all properties for a database.

        Args:
            database_id: Database ID

        Returns:
            List of Property instances ordered by position
        """
        stmt = (
            select(Property)
            .where(Property.database_id == database_id)
            .order_by(Property.position)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def bulk_get_by_ids(
        self,
        property_ids: list[uuid.UUID],
    ) -> list[Property]:
        """Fetch multiple properties by ID.

        Used by query engine for filter/sort validation.

        Args:
            property_ids: List of property IDs

        Returns:
            List of Property instances
        """
        if not property_ids:
            return []

        stmt = select(Property).where(Property.id.in_(property_ids))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete(self, prop: Property) -> None:
        """Delete a property.

        Args:
            prop: Property instance to delete
        """
        await self.session.delete(prop)
        await self.session.flush()
