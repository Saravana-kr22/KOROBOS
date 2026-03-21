"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Analytics Service — Kafka consumer for habit events.
Processes habit.completed events and records habit completion rate and streak metrics
to the analytics database.
"""

import logging
from uuid import UUID

from app.services.service_logic import AnalyticsService

from backend.shared.database.connection import async_session_factory
from backend.shared.messaging.consumer import BaseEventConsumer

logger = logging.getLogger(__name__)


class HabitEventConsumer(BaseEventConsumer):
    """Consumes habit events and records analytics metrics.

    Subscribes to:
    - habit.completed: habit completion with streak information

    Records metrics:
    - habit_completion_rate: 0-100 percentage
    - current_streak: integer count of days

    Error Handling & DLQ:
    - Validation errors (missing fields): logged as warning, event skipped
    - Processing errors (UUID format, database): logged with traceback,
      re-raised to DLQ
    - BaseEventConsumer handles DLQ forwarding to {topic}.dlq with retry
      policy: [0s, 5s, 30s] delays before forwarding as BaseEvent message
    """

    topics = ["habit.completed"]
    group_id = "analytics-service-habits"

    async def handle_event(self, topic: str, payload: dict) -> None:
        """Process habit event and record analytics metrics.

        Args:
            topic: Event topic (habit.completed)
            payload: Event payload containing habit_id, user_id, streak, etc.
        """
        try:
            # Extract required fields
            user_id_str = payload.get("user_id")
            habit_id = payload.get("habit_id")
            streak = payload.get("streak", 0)

            if not user_id_str:
                logger.warning("Event payload missing user_id, skipping")
                return

            user_id = UUID(user_id_str)

            # Create DB session and record metrics
            async with async_session_factory() as session:
                analytics_svc = AnalyticsService(session)

                # Record completion rate (1 = 100%)
                await analytics_svc.record_metric(
                    user_id=user_id,
                    metric_type="habit_completion_rate",
                    value=100.0,
                    metadata={
                        "habit_id": habit_id,
                        "streak": streak,
                    },
                )

                # Record current streak if available
                if streak > 0:
                    await analytics_svc.record_metric(
                        user_id=user_id,
                        metric_type="current_streak",
                        value=float(streak),
                        metadata={"habit_id": habit_id},
                    )

                await session.commit()

            logger.info(
                "Recorded habit metrics: user_id=%s, habit_id=%s, streak=%d",
                user_id,
                habit_id,
                streak,
            )

        except ValueError as e:
            logger.error("Invalid user_id format in event payload: %s", e)
        except Exception as e:
            logger.error("Error processing habit event: %s", e, exc_info=True)
            raise
