"""
KOROBOS — Database Service Record Repository

Data access layer for records and record values.
"""

import uuid
from typing import Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from backend.services.database_service.app.models.record_model import (
    Record,
    RecordValue,
)


class RecordRepository:
    """Repository for record and record value CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        database_id: uuid.UUID,
        note_id: Optional[uuid.UUID] = None,
    ) -> Record:
        """Create a new record.

        Args:
            database_id: Parent database ID
            note_id: Optional link to a note

        Returns:
            Created Record instance
        """
        record = Record(
            database_id=database_id,
            note_id=note_id,
        )
        self.session.add(record)
        await self.session.flush()
        return record

    async def get_by_id(self, record_id: uuid.UUID) -> Optional[Record]:
        """Fetch a record by ID with eager-loaded values.

        Args:
            record_id: Record ID

        Returns:
            Record instance or None if not found
        """
        stmt = (
            select(Record)
            .where(Record.id == record_id)
            .options(joinedload(Record.values))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_database(
        self,
        database_id: uuid.UUID,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Record], int]:
        """Fetch paginated records for a database.

        Args:
            database_id: Database ID
            offset: Query offset
            limit: Max results per page

        Returns:
            Tuple of (records, total_count)
        """
        # Count total
        count_stmt = (
            select(func.count())
            .select_from(Record)
            .where(Record.database_id == database_id)
        )
        total = await self.session.execute(count_stmt)
        total_count = total.scalar_one()

        # Fetch paginated with values
        stmt = (
            select(Record)
            .where(Record.database_id == database_id)
            .order_by(Record.created_at.desc())
            .offset(offset)
            .limit(limit)
            .options(joinedload(Record.values))
        )
        result = await self.session.execute(stmt)
        records = result.scalars().unique().all()

        return list(records), total_count

    async def update_timestamps(self, record: Record) -> Record:
        """Update record's updated_at timestamp.

        Args:
            record: Record instance

        Returns:
            Updated Record instance
        """
        from datetime import datetime

        record.updated_at = datetime.utcnow()
        await self.session.flush()
        return record

    async def delete(self, record: Record) -> None:
        """Delete a record (cascade removes record_values).

        Args:
            record: Record instance to delete
        """
        await self.session.delete(record)
        await self.session.flush()

    async def upsert_value(
        self,
        record_id: uuid.UUID,
        property_id: uuid.UUID,
        value: Optional[str],
    ) -> RecordValue:
        """Create or update a record value.

        Uses composite key (record_id, property_id) to upsert.

        Args:
            record_id: Record ID
            property_id: Property ID
            value: Field value (as string)

        Returns:
            Created or updated RecordValue instance
        """
        # Try to fetch existing
        stmt = select(RecordValue).where(
            and_(
                RecordValue.record_id == record_id,
                RecordValue.property_id == property_id,
            )
        )
        result = await self.session.execute(stmt)
        rv = result.scalar_one_or_none()

        if rv:
            rv.value = value
        else:
            rv = RecordValue(
                record_id=record_id,
                property_id=property_id,
                value=value,
            )
            self.session.add(rv)

        await self.session.flush()
        return rv

    async def delete_values(self, record_id: uuid.UUID) -> None:
        """Delete all values for a record.

        Args:
            record_id: Record ID
        """
        stmt = select(RecordValue).where(RecordValue.record_id == record_id)
        result = await self.session.execute(stmt)
        values = result.scalars().all()
        for rv in values:
            await self.session.delete(rv)
        await self.session.flush()
