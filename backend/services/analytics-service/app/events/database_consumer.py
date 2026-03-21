"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Analytics Service — Kafka consumer for database events.
Processes record.created events and records data activity metrics
to the analytics database.
"""

import logging
from uuid import UUID

from app.services.service_logic import AnalyticsService

from backend.shared.database.connection import async_session_factory
from backend.shared.messaging.consumer import BaseEventConsumer

logger = logging.getLogger(__name__)


class DatabaseEventConsumer(BaseEventConsumer):
    """Consumes database events and records analytics metrics.

    Subscribes to:
    - record.created: database record creation event

    Records metrics:
    - records_created: count of records (1.0 per event)

    Error Handling & DLQ:
    - Validation errors (missing fields): logged as warning, event skipped
    - Processing errors (UUID format, database): logged with traceback,
      re-raised to DLQ
    - BaseEventConsumer handles DLQ forwarding to {topic}.dlq with retry
      policy: [0s, 5s, 30s] delays before forwarding as BaseEvent message
    """

    topics = ["record.created"]
    group_id = "analytics-service-database"

    async def handle_event(self, topic: str, payload: dict) -> None:
        """Process database event and record analytics metrics.

        Args:
            topic: Event topic (record.created)
            payload: Event payload containing record_id, user_id, database_id, etc.
        """
        try:
            # Extract required fields
            user_id_str = payload.get("user_id")
            record_id = payload.get("record_id")
            database_id = payload.get("database_id")

            if not user_id_str:
                logger.warning("Event payload missing user_id, skipping")
                return

            user_id = UUID(user_id_str)

            # Create DB session and record metric
            async with async_session_factory() as session:
                analytics_svc = AnalyticsService(session)
                await analytics_svc.record_metric(
                    user_id=user_id,
                    metric_type="records_created",
                    value=1.0,
                    metadata={
                        "record_id": record_id,
                        "database_id": database_id,
                    },
                )
                await session.commit()

            logger.info(
                "Recorded database metric: user_id=%s, record_id=%s, database_id=%s",
                user_id,
                record_id,
                database_id,
            )

        except ValueError as e:
            logger.error("Invalid user_id format in event payload: %s", e)
        except Exception as e:
            logger.error("Error processing database event: %s", e, exc_info=True)
            raise
