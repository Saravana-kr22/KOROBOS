"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Analytics Service — Kafka consumer for learning events.
Processes learning.session.completed and learning.session.logged events
and records learning_hours metrics to the analytics database.
"""

import logging
from uuid import UUID

from app.services.service_logic import AnalyticsService

from backend.shared.database.connection import async_session_factory
from backend.shared.messaging.consumer import BaseEventConsumer

logger = logging.getLogger(__name__)


class LearningEventConsumer(BaseEventConsumer):
    """Consumes learning events and records analytics metrics.

    Subscribes to:
    - learning.session.completed: full session with duration
    - learning.session.logged: manually logged session with duration

    Records metric: learning_hours = duration_minutes / 60.0

    Error Handling & DLQ:
    - Validation errors (missing fields): logged as warning, event skipped
    - Processing errors (UUID format, database): logged with traceback,
      re-raised to DLQ
    - BaseEventConsumer handles DLQ forwarding to {topic}.dlq with retry
      policy: [0s, 5s, 30s] delays before forwarding as BaseEvent message
    """

    topics = ["learning.session.completed", "learning.session.logged"]
    group_id = "analytics-service-learning"

    async def handle_event(self, topic: str, payload: dict) -> None:
        """Process learning event and record analytics metric.

        Args:
            topic: Event topic (learning.session.completed or learning.session.logged)
            payload: Event payload containing session_id, user_id, topic, duration, etc.
        """
        try:
            # Extract required fields
            user_id_str = payload.get("user_id")
            duration_minutes = payload.get("duration")
            session_id = payload.get("session_id")
            session_topic = payload.get("topic")

            if not user_id_str:
                logger.warning("Event payload missing user_id, skipping")
                return

            if duration_minutes is None:
                logger.warning("Event payload missing duration, skipping")
                return

            user_id = UUID(user_id_str)
            duration_hours = duration_minutes / 60.0

            # Create DB session and record metric
            async with async_session_factory() as session:
                analytics_svc = AnalyticsService(session)
                await analytics_svc.record_metric(
                    user_id=user_id,
                    metric_type="learning_hours",
                    value=duration_hours,
                    metadata={
                        "session_id": session_id,
                        "topic": session_topic,
                        "duration_minutes": duration_minutes,
                    },
                )
                await session.commit()

            logger.info(
                "Recorded learning_hours metric: user_id=%s, hours=%.2f, topic=%s",
                user_id,
                duration_hours,
                session_topic,
            )

        except ValueError as e:
            logger.error("Invalid user_id format in event payload: %s", e)
        except Exception as e:
            logger.error("Error processing learning event: %s", e, exc_info=True)
            raise
