"""
KOROBOS — Database Event Handlers

Shared event handlers for database service events.
Consumed by: search-worker, ai-worker
"""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


async def handle_record_created(event: dict[str, Any]) -> None:
    """Handle record.created event for indexing and AI processing.

    Args:
        event: Database event from Kafka
    """
    try:
        payload = event.get("payload", {})
        record_id = payload.get("record_id")
        database_id = payload.get("database_id")
        user_id = payload.get("user_id")
        values = payload.get("values", {})

        logger.info(
            f"Processing record.created: record={record_id} database={database_id}"
        )

        # Build searchable content from record values
        searchable_content = " ".join(str(v) for v in values.values() if v)

        # Emit to search indexer
        await _emit_search_event(
            action="index",
            doc_type="record",
            doc_id=record_id,
            content=searchable_content,
            metadata={
                "record_id": record_id,
                "database_id": database_id,
                "user_id": user_id,
            },
        )

        # Emit to AI processor
        await _emit_ai_event(
            action="analyze",
            entity_type="record",
            entity_id=record_id,
            data={
                "database_id": database_id,
                "user_id": user_id,
                "values": values,
            },
        )

    except Exception as exc:
        logger.error(f"Error handling record.created: {exc}", exc_info=True)


async def handle_record_updated(event: dict[str, Any]) -> None:
    """Handle record.updated event for re-indexing and AI insights.

    Args:
        event: Database event from Kafka
    """
    try:
        payload = event.get("payload", {})
        record_id = payload.get("record_id")
        database_id = payload.get("database_id")
        values = payload.get("values", {})

        logger.info(
            f"Processing record.updated: record={record_id} database={database_id}"
        )

        # Rebuild searchable content
        searchable_content = " ".join(str(v) for v in values.values() if v)

        # Re-index in search
        await _emit_search_event(
            action="update",
            doc_type="record",
            doc_id=record_id,
            content=searchable_content,
            metadata={"database_id": database_id, "record_id": record_id},
        )

        # Re-analyze with AI
        await _emit_ai_event(
            action="analyze",
            entity_type="record",
            entity_id=record_id,
            data={"database_id": database_id, "values": values},
        )

    except Exception as exc:
        logger.error(f"Error handling record.updated: {exc}", exc_info=True)


async def handle_record_deleted(event: dict[str, Any]) -> None:
    """Handle record.deleted event for deindexing.

    Args:
        event: Database event from Kafka
    """
    try:
        payload = event.get("payload", {})
        record_id = payload.get("record_id")
        database_id = payload.get("database_id")

        logger.info(
            f"Processing record.deleted: record={record_id} database={database_id}"
        )

        # Remove from search index
        await _emit_search_event(
            action="delete",
            doc_type="record",
            doc_id=record_id,
            metadata={"database_id": database_id},
        )

    except Exception as exc:
        logger.error(f"Error handling record.deleted: {exc}", exc_info=True)


async def handle_database_created(event: dict[str, Any]) -> None:
    """Handle database.created event for AI metadata.

    Args:
        event: Database event from Kafka
    """
    try:
        payload = event.get("payload", {})
        database_id = payload.get("database_id")
        user_id = payload.get("user_id")
        name = payload.get("name")

        logger.info(
            f"Processing database.created: database={database_id} user={user_id}"
        )

        # Emit to AI for user insights
        await _emit_ai_event(
            action="track_event",
            entity_type="database",
            entity_id=database_id,
            data={
                "user_id": user_id,
                "database_name": name,
                "event": "database_created",
            },
        )

    except Exception as exc:
        logger.error(f"Error handling database.created: {exc}", exc_info=True)


async def _emit_search_event(
    action: str,
    doc_type: str,
    doc_id: str,
    content: str = "",
    metadata: Optional[dict[str, Any]] = None,
) -> None:
    """Emit event to search indexer.

    TODO: Implement actual Kafka publish to search-worker topic.
    For now, just logs.
    """
    logger.debug(f"SEARCH: {action} {doc_type} {doc_id} (content_len={len(content)})")
    # This would publish to "search.index" or similar Kafka topic


async def _emit_ai_event(
    action: str,
    entity_type: str,
    entity_id: str,
    data: Optional[dict[str, Any]] = None,
) -> None:
    """Emit event to AI processor.

    TODO: Implement actual Kafka publish to ai-worker topic.
    For now, just logs.
    """
    logger.debug(f"AI: {action} {entity_type} {entity_id}")
    # This would publish to "ai.insights" or similar Kafka topic


# Event router
EVENT_HANDLERS = {
    "record.created": handle_record_created,
    "record.updated": handle_record_updated,
    "record.deleted": handle_record_deleted,
    "database.created": handle_database_created,
}


async def handle_event(event: dict[str, Any]) -> None:
    """Route database events to appropriate handlers.

    Args:
        event: Event from Kafka with event_type field
    """
    event_type = event.get("event_type")

    if event_type not in EVENT_HANDLERS:
        logger.debug(f"Skipping unhandled event type: {event_type}")
        return

    handler = EVENT_HANDLERS[event_type]
    await handler(event)
