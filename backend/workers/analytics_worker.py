"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Analytics Worker

Consumes activity events from Kafka and records analytics metrics in the
Analytics Service database, forming the backbone of the analytics
pipeline described in Sprint 4.
"""

import asyncio
import importlib
from typing import Any
from uuid import UUID

from backend.shared.database.connection import async_session_factory
from backend.shared.logging.logger import get_logger
from backend.shared.messaging.consumer import BaseEventConsumer
from backend.shared.messaging.schemas import BaseEvent
from backend.workers.event_transforms import analytics_metric_for_event
from backend.workers.service_loader import configure_service_app_path
from backend.workers.topics import ANALYTICS_TOPICS

configure_service_app_path("analytics-service")
AnalyticsRepository = importlib.import_module(
    "app.repositories.repository"
).AnalyticsRepository

logger = get_logger("analytics-worker")


class AnalyticsEventConsumer(BaseEventConsumer):
    """
    Consumer for core activity topics that drive analytics:
      - note.created
      - note.link.created
      - habit.created
      - habit.completed
      - learning.session.logged
      - meal.logged
      - workout.logged
      - user.registered
      - user.login
      - ai.interaction.completed
    """

    async def handle_event(self, topic: str, payload: dict[str, Any]):
        event = BaseEvent.model_validate(payload)
        event_type = event.event_type
        data = event.payload

        # Many metrics are keyed by user_id; skip if missing.
        user_id_raw = data.get("user_id")
        if not user_id_raw:
            logger.warning("Skipping analytics event without user_id: %s", event_type)
            return

        user_id = UUID(user_id_raw)
        metric = analytics_metric_for_event(event_type, data)
        if metric is None:
            logger.debug("Ignoring unmapped analytics event_type: %s", event_type)
            return
        metric_type, value = metric

        async with async_session_factory() as session:
            repo = AnalyticsRepository(session)
            await repo.create(
                user_id=user_id,
                metric_type=metric_type,
                value=value,
                metadata_json={"source_event": event_type},
            )
            await session.commit()


async def main() -> None:
    consumer = AnalyticsEventConsumer(
        topics=list(ANALYTICS_TOPICS),
        group_id="analytics-group",
    )
    await consumer.start()

    logger.info("Analytics worker started")
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Analytics worker shutting down")
        await consumer.stop()


if __name__ == "__main__":
    asyncio.run(main())
