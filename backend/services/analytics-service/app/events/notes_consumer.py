"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Analytics Service — Kafka consumer for notes events.
Processes note.created events and records knowledge activity metrics
to the analytics database.
"""

import logging
from uuid import UUID

from app.services.service_logic import AnalyticsService

from backend.shared.database.connection import async_session_factory
from backend.shared.messaging.consumer import BaseEventConsumer

logger = logging.getLogger(__name__)


class NotesEventConsumer(BaseEventConsumer):
    """Consumes notes events and records analytics metrics.

    Subscribes to:
    - note.created: note creation event

    Records metrics:
    - notes_created: count of notes (1.0 per event)
    - (optional) linking_density: number of backlinks in note

    Error Handling & DLQ:
    - Validation errors (missing fields): logged as warning, event skipped
    - Processing errors (UUID format, database): logged with traceback,
      re-raised to DLQ
    - BaseEventConsumer handles DLQ forwarding to {topic}.dlq with retry
      policy: [0s, 5s, 30s] delays before forwarding as BaseEvent message
    """

    topics = ["note.created"]
    group_id = "analytics-service-notes"

    async def handle_event(self, topic: str, payload: dict) -> None:
        """Process notes event and record analytics metrics.

        Args:
            topic: Event topic (note.created)
            payload: Event payload containing note_id, user_id, backlinks, etc.
        """
        try:
            # Extract required fields
            user_id_str = payload.get("user_id")
            note_id = payload.get("note_id")
            backlinks = payload.get("backlinks", 0)

            if not user_id_str:
                logger.warning("Event payload missing user_id, skipping")
                return

            user_id = UUID(user_id_str)

            # Create DB session and record metric
            async with async_session_factory() as session:
                analytics_svc = AnalyticsService(session)
                await analytics_svc.record_metric(
                    user_id=user_id,
                    metric_type="notes_created",
                    value=1.0,
                    metadata={
                        "note_id": note_id,
                        "backlinks": backlinks,
                    },
                )
                await session.commit()

            logger.info(
                "Recorded notes metric: user_id=%s, note_id=%s, backlinks=%d",
                user_id,
                note_id,
                backlinks,
            )

        except ValueError as e:
            logger.error("Invalid user_id format in event payload: %s", e)
        except Exception as e:
            logger.error("Error processing notes event: %s", e, exc_info=True)
            raise
