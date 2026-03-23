"""
KOROBOS — Database Service Repository Layer

Data access layer for databases.
"""

import uuid
from typing import Optional

from app.models.database_model import Database
from app.models.record_model import Record
from sqlalchemy import delete as sql_delete
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class DatabaseRepository:
    """Repository for database CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: uuid.UUID,
        name: str,
        icon: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Database:
        """Create a new database.

        Args:
            user_id: Owner of the database
            name: Database name
            icon: Optional icon/emoji identifier
            description: Optional description

        Returns:
            Created Database instance
        """
        db = Database(
            user_id=user_id,
            name=name,
            icon=icon,
            description=description,
        )
        self.session.add(db)
        await self.session.flush()
        # Re-fetch with relationships eagerly loaded
        result = await self.session.execute(
            select(Database)
            .options(selectinload(Database.properties), selectinload(Database.records))
            .where(Database.id == db.id)
        )
        return result.scalar_one()

    async def get_by_id(self, db_id: uuid.UUID) -> Optional[Database]:
        """Fetch a database by ID with eager-loaded properties.

        Args:
            db_id: Database ID

        Returns:
            Database instance or None if not found
        """
        stmt = (
            select(Database)
            .options(selectinload(Database.properties), selectinload(Database.records))
            .where(Database.id == db_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        user_id: uuid.UUID,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Database], int]:
        """Fetch paginated databases for a user.

        Args:
            user_id: User ID
            offset: Query offset
            limit: Max results per page

        Returns:
            Tuple of (databases, total_count)
        """
        # Count total
        count_stmt = (
            select(func.count())
            .select_from(Database)
            .where(Database.user_id == user_id)
        )
        total = await self.session.execute(count_stmt)
        total_count = total.scalar_one()

        # Fetch paginated with eager-loaded relationships
        stmt = (
            select(Database)
            .options(selectinload(Database.properties), selectinload(Database.records))
            .where(Database.user_id == user_id)
            .order_by(Database.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        databases = result.scalars().all()

        return list(databases), total_count

    async def update(
        self,
        db: Database,
        **kwargs,
    ) -> Database:
        """Update database fields.

        Args:
            db: Database instance to update
            **kwargs: Fields to update

        Returns:
            Updated Database instance
        """
        for key, value in kwargs.items():
            if value is not None and hasattr(db, key):
                setattr(db, key, value)
        await self.session.flush()
        # Reload with relationships after update
        return await self.get_by_id(db.id)

    async def delete(self, db: Database) -> None:
        """Delete a database.

        Args:
            db: Database instance to delete
        """
        # Explicitly delete child records first (SQLite doesn't enforce FK
        # cascades by default)
        await self.session.execute(
            sql_delete(Record).where(Record.database_id == db.id)
        )
        await self.session.delete(db)
        await self.session.flush()
