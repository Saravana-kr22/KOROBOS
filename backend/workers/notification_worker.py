"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Notification Worker

Consumes events from Kafka and creates in-app and push notifications,
wiring the notification pipeline described in Sprint 4.
"""

import asyncio
import importlib
from typing import Any
from uuid import UUID

import aiohttp

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
PushTokenRepository = importlib.import_module(
    "app.repositories.push_token_repository"
).PushTokenRepository

logger = get_logger("notification-worker")


class NotificationEventConsumer(BaseEventConsumer):
    """
    Consumer for events that should trigger user-facing notifications.

    Handles:
      - habit.completed → in-app notification
      - habit.reminder.due → in-app + push notification
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

            # For reminder events, also send push notification if tokens exist
            if event_type == "habit.reminder.due":
                await self._send_push_notifications(user_id, title, body, session)

    async def _send_push_notifications(
        self, user_id: UUID, title: str, body: str, session
    ) -> None:
        """Send push notifications to all registered tokens for a user."""
        push_repo = PushTokenRepository(session)
        push_tokens = await push_repo.get_by_user(user_id)

        if not push_tokens:
            return

        async with aiohttp.ClientSession() as http_session:
            for push_token in push_tokens:
                await self._send_expo_push(http_session, push_token.token, title, body)

    async def _send_expo_push(
        self, session: aiohttp.ClientSession, token: str, title: str, body: str
    ) -> None:
        """Send a single push notification via Expo Push API."""
        try:
            payload = {"to": token, "title": title, "body": body}
            async with session.post(
                "https://exp.host/--/api/v2/push/send", json=payload
            ) as resp:
                if resp.status != 200:
                    logger.warning(
                        f"Expo push failed for {token[:10]}...: {resp.status}"
                    )
        except Exception as exc:
            logger.error(f"Error sending Expo push notification: {exc}")


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
