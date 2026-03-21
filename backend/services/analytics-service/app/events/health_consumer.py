"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Analytics Service — Kafka consumer for health events.
Processes meal.logged and workout.logged events and records calorie metrics
to the analytics database.
"""

import logging
from uuid import UUID

from app.services.service_logic import AnalyticsService

from backend.shared.database.connection import async_session_factory
from backend.shared.messaging.consumer import BaseEventConsumer

logger = logging.getLogger(__name__)


class HealthEventConsumer(BaseEventConsumer):
    """Consumes health events and records analytics metrics.

    Subscribes to:
    - meal.logged: meal creation with calorie count
    - workout.logged: workout completion with calories burned

    Records metrics:
    - calorie_intake: calories consumed from meals
    - calorie_burned: calories burned from workouts

    Error Handling & DLQ:
    - Validation errors (missing fields): logged as warning, event skipped
    - Processing errors (UUID format, database): logged with traceback,
      re-raised to DLQ
    - BaseEventConsumer handles DLQ forwarding to {topic}.dlq with retry
      policy: [0s, 5s, 30s] delays before forwarding as BaseEvent message
    """

    topics = ["meal.logged", "workout.logged"]
    group_id = "analytics-service-health"

    async def handle_event(self, topic: str, payload: dict) -> None:
        """Process health event and record analytics metrics.

        Args:
            topic: Event topic (meal.logged or workout.logged)
            payload: Event payload containing user_id, calories, etc.
        """
        try:
            # Extract required fields
            user_id_str = payload.get("user_id")
            calories = payload.get("calories", 0)

            if not user_id_str:
                logger.warning("Event payload missing user_id, skipping")
                return

            if calories is None or calories < 0:
                logger.warning("Event payload missing or invalid calories, skipping")
                return

            user_id = UUID(user_id_str)

            # Determine metric type based on topic
            if topic == "meal.logged":
                metric_type = "calorie_intake"
                metadata_key = "meal_id"
            else:  # workout.logged
                metric_type = "calorie_burned"
                metadata_key = "workout_id"

            item_id = payload.get(metadata_key)

            # Create DB session and record metric
            async with async_session_factory() as session:
                analytics_svc = AnalyticsService(session)
                await analytics_svc.record_metric(
                    user_id=user_id,
                    metric_type=metric_type,
                    value=float(calories),
                    metadata={metadata_key: item_id},
                )
                await session.commit()

            logger.info(
                "Recorded health metric: user_id=%s, metric=%s, value=%f",
                user_id,
                metric_type,
                calories,
            )

        except ValueError as e:
            logger.error("Invalid user_id format in event payload: %s", e)
        except Exception as e:
            logger.error("Error processing health event: %s", e, exc_info=True)
            raise
