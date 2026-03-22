"""
KOROBOS — Database Service Record Operations

Business logic for record CRUD operations.
"""

import logging
import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.database_service.app.models.record_model import Record
from backend.services.database_service.app.repositories.property_repository import (
    PropertyRepository,
)
from backend.services.database_service.app.repositories.record_repository import (
    RecordRepository,
)
from backend.services.database_service.app.schemas.database_schema import (
    RecordCreate,
    RecordFilter,
    RecordSort,
    RecordUpdate,
)
from backend.services.database_service.app.services.query_engine import QueryEngine
from backend.services.database_service.app.services.type_validator import (
    TypeValidator,
    ValidationError,
)
from backend.shared.messaging.producer import publish_event

logger = logging.getLogger(__name__)


class RecordService:
    """Service for record operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.record_repo = RecordRepository(session)
        self.prop_repo = PropertyRepository(session)
        self.query_engine = QueryEngine(session)

    async def create_record(
        self,
        database_id: uuid.UUID,
        user_id: uuid.UUID,
        data: RecordCreate,
    ) -> Record:
        """Create a new record.

        Validates that all properties belong to the database,
        validates property values against their types,
        creates the record and its values, publishes a kafka event.

        Args:
            database_id: Parent database ID
            user_id: User creating the record
            data: Record creation data

        Returns:
            Created Record instance with values

        Raises:
            ValueError: If property IDs don't belong to database or values invalid
        """
        # Validate property IDs and fetch properties
        if data.values:
            prop_ids = [uuid.UUID(pid) for pid in data.values.keys()]
            props = await self.prop_repo.bulk_get_by_ids(prop_ids)
            prop_dict = {p.id: p for p in props}

            for pid in prop_ids:
                if pid not in prop_dict:
                    raise ValueError(f"Property {pid} not found")
                if prop_dict[pid].database_id != database_id:
                    raise ValueError(
                        f"Property {pid} does not belong to database {database_id}"
                    )

            # Validate values against property types
            for prop_id_str, value in data.values.items():
                prop_id = uuid.UUID(prop_id_str)
                prop = prop_dict[prop_id]
                try:
                    # Validate value against property type
                    TypeValidator.validate(
                        value=value,
                        property_name=prop.name,
                        property_type=prop.type,
                        options=prop.options,
                    )
                except ValidationError as e:
                    logger.warning(f"Validation error: {e}")
                    raise ValueError(str(e))

        # Create record
        note_id = uuid.UUID(data.note_id) if data.note_id else None
        record = await self.record_repo.create(
            database_id=database_id,
            note_id=note_id,
        )

        # Upsert values
        for prop_id_str, value in data.values.items():
            prop_id = uuid.UUID(prop_id_str)
            await self.record_repo.upsert_value(
                record_id=record.id,
                property_id=prop_id,
                value=value,
            )

        # Reload to include values
        record = await self.record_repo.get_by_id(record.id)

        # Publish event
        from backend.services.database_service.app.events.database_events import (
            RecordCreatedEvent,
        )

        # Prepare event payload for graph integration
        event_payload = {
            "record_id": str(record.id),
            "database_id": str(database_id),
            "user_id": str(user_id),
            "database_name": data.database_name
            if hasattr(data, "database_name")
            else f"Record {record.id}",
            "values": data.values,
        }

        # Add related note if linked
        if note_id:
            event_payload["related_note_id"] = str(note_id)

        event = RecordCreatedEvent(payload=event_payload)
        try:
            await publish_event(event, key=str(user_id))
        except Exception as e:
            logger.warning(f"Failed to publish record.created event: {e}")

        return record

    async def get_record(
        self,
        record_id: uuid.UUID,
    ) -> Optional[Record]:
        """Fetch a record by ID.

        Args:
            record_id: Record ID

        Returns:
            Record instance or None if not found
        """
        return await self.record_repo.get_by_id(record_id)

    async def list_records(
        self,
        database_id: uuid.UUID,
        filters: Optional[list[RecordFilter]] = None,
        sort: Optional[RecordSort] = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[Record], int]:
        """List records with optional filtering, sorting, pagination.

        Args:
            database_id: Database ID
            filters: Filter specifications
            sort: Sort specification
            page: Page number (1-indexed)
            limit: Results per page

        Returns:
            Tuple of (records, total_count)
        """
        return await self.query_engine.query_records(
            database_id=database_id,
            filters=filters,
            sort=sort,
            page=page,
            limit=limit,
        )

    async def update_record(
        self,
        record: Record,
        user_id: uuid.UUID,
        data: RecordUpdate,
    ) -> Record:
        """Update a record's values.

        Validates properties belong to the database, validates values against types,
        upserts values, publishes a Kafka event.

        Args:
            record: Record instance to update
            user_id: User updating the record
            data: Update data

        Returns:
            Updated Record instance

        Raises:
            ValueError: If property IDs don't belong to database or values invalid
        """
        # Validate property IDs and fetch properties
        if data.values:
            prop_ids = [uuid.UUID(pid) for pid in data.values.keys()]
            props = await self.prop_repo.bulk_get_by_ids(prop_ids)
            prop_dict = {p.id: p for p in props}

            for pid in prop_ids:
                if pid not in prop_dict:
                    raise ValueError(f"Property {pid} not found")
                if prop_dict[pid].database_id != record.database_id:
                    raise ValueError(
                        f"Property {pid} does not belong to "
                        f"database {record.database_id}"
                    )

            # Validate values against property types
            for prop_id_str, value in data.values.items():
                prop_id = uuid.UUID(prop_id_str)
                prop = prop_dict[prop_id]
                try:
                    # Validate value against property type
                    TypeValidator.validate(
                        value=value,
                        property_name=prop.name,
                        property_type=prop.type,
                        options=prop.options,
                    )
                except ValidationError as e:
                    logger.warning(f"Validation error: {e}")
                    raise ValueError(str(e))

        # Upsert values
        for prop_id_str, value in data.values.items():
            prop_id = uuid.UUID(prop_id_str)
            await self.record_repo.upsert_value(
                record_id=record.id,
                property_id=prop_id,
                value=value,
            )

        # Update timestamps
        record = await self.record_repo.update_timestamps(record)

        # Reload with values
        record = await self.record_repo.get_by_id(record.id)

        # Publish event
        from backend.services.database_service.app.events.database_events import (
            RecordUpdatedEvent,
        )

        event = RecordUpdatedEvent(
            payload={
                "record_id": str(record.id),
                "database_id": str(record.database_id),
                "user_id": str(user_id),
                "values": data.values,
            }
        )
        try:
            await publish_event(event, key=str(user_id))
        except Exception as e:
            logger.warning(f"Failed to publish record.updated event: {e}")

        return record

    async def delete_record(
        self,
        record: Record,
        user_id: uuid.UUID,
    ) -> None:
        """Delete a record.

        Cascade removes record_values, publishes Kafka event.

        Args:
            record: Record instance to delete
            user_id: User deleting the record
        """
        record_id = record.id
        database_id = record.database_id

        await self.record_repo.delete(record)

        # Publish event
        from backend.services.database_service.app.events.database_events import (
            RecordDeletedEvent,
        )

        event = RecordDeletedEvent(
            payload={
                "record_id": str(record_id),
                "database_id": str(database_id),
                "user_id": str(user_id),
            }
        )
        try:
            await publish_event(event, key=str(user_id))
        except Exception as e:
            logger.warning(f"Failed to publish record.deleted event: {e}")
