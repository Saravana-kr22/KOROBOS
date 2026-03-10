"""
Notification Worker

Consumes habit completion events from Kafka and creates in-app
notifications, wiring the notification pipeline described in Sprint 4.
"""

import asyncio
import importlib
from typing import Any
from uuid import UUID

from backend.shared.database.connection import async_session_factory
from backend.shared.logging.logger import get_logger
from backend.shared.messaging.consumer import BaseEventConsumer
from backend.shared.messaging.schemas import BaseEvent
from backend.workers.event_transforms import notification_content_for_event
from backend.workers.service_loader import configure_service_app_path
from backend.workers.topics import NOTIFICATION_TOPICS

configure_service_app_path("notification-service")
NotificationRepository = importlib.import_module(
    "app.repositories.repository"
).NotificationRepository

logger = get_logger("notification-worker")


class NotificationEventConsumer(BaseEventConsumer):
    """
    Consumer for events that should trigger user-facing notifications.

    Initial scope:
      - habit.completed → create a simple in-app reminder/celebration.
    """

    async def handle_event(self, topic: str, payload: dict[str, Any]):
        event = BaseEvent.model_validate(payload)
        event_type = event.event_type
        data = event.payload

        notification = notification_content_for_event(event_type, data)
        if notification is None:
            logger.debug("Ignoring non-notification event_type: %s", event_type)
            return

        user_id_raw = data.get("user_id")
        if not user_id_raw:
            logger.warning("Skipping notification event without user_id")
            return

        user_id = UUID(user_id_raw)
        title, body = notification

        async with async_session_factory() as session:
            repo = NotificationRepository(session)
            await repo.create(
                user_id=user_id,
                title=title,
                body=body,
                channel="in_app",
            )
            await session.commit()


async def main() -> None:
    consumer = NotificationEventConsumer(
        topics=list(NOTIFICATION_TOPICS),
        group_id="notification-group",
    )
    await consumer.start()

    logger.info("Notification worker started")
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Notification worker shutting down")
        await consumer.stop()


if __name__ == "__main__":
    asyncio.run(main())
