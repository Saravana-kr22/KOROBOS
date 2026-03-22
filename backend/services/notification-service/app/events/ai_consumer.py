"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Notification Service — AI Consumer

Consumes AIInteractionCompletedEvent and sends push notifications.
"""

import logging
from uuid import UUID

from app.schemas.schema import NotificationCreate
from app.services.service_logic import NotificationService

from backend.shared.database.connection import async_session_factory
from backend.shared.messaging.consumer import BaseEventConsumer

logger = logging.getLogger(__name__)


class AIInteractionConsumer(BaseEventConsumer):
    """Consumes AI interaction completion events and sends notifications.

    Subscribes to:
    - ai.interaction.completed: when AI generates recommendations or summaries

    For recommendations and summaries, sends push notifications to users
    with the AI-generated content.

    Error Handling & DLQ:
    - Validation errors: logged as warning, event skipped
    - Processing errors: logged with traceback, re-raised to DLQ
    """

    topics = ["ai.interaction.completed"]
    group_id = "notification-ai-consumer"

    async def handle_event(self, topic: str, payload: dict) -> None:
        """Process AI interaction completion event and send notification.

        Args:
            topic: Event topic (ai.interaction.completed)
            payload: Event payload containing interaction_id, user_id, type, etc.
        """
        try:
            # Extract required fields
            user_id_str = payload.get("user_id")
            interaction_type = payload.get("type")

            if not user_id_str:
                logger.warning("Event payload missing user_id, skipping")
                return

            if not interaction_type:
                logger.warning("Event payload missing interaction type, skipping")
                return

            # Only send notifications for recommendations and summaries
            if interaction_type not in ["recommendation", "summary"]:
                logger.debug(
                    f"Skipping notification for interaction type: {interaction_type}"
                )
                return

            user_id = UUID(user_id_str)

            # Map interaction types to notification titles
            title_map = {
                "recommendation": "💡 New Recommendation",
                "summary": "📋 AI Summary Available",
            }

            title = title_map.get(interaction_type, "🤖 AI Insight")
            body = self._get_notification_body(interaction_type)

            # Send notification via notification service
            async with async_session_factory() as session:
                notif_svc = NotificationService(session)
                notification = await notif_svc.send_notification(
                    user_id,
                    NotificationCreate(
                        title=title,
                        body=body,
                        channel="push",
                    ),
                )
                await session.commit()

            logger.info(
                "Sent push notification: user_id=%s, type=%s, notification_id=%s",
                user_id,
                interaction_type,
                notification.id,
            )

        except ValueError as e:
            logger.error("Invalid user_id format in event payload: %s", e)
        except Exception as e:
            logger.error(
                "Error processing AI event in notification consumer: %s",
                e,
                exc_info=True,
            )
            raise

    def _get_notification_body(self, interaction_type: str) -> str:
        """Generate notification body based on interaction type."""
        bodies = {
            "recommendation": "Check out your personalized recommendations.",
            "summary": "View your AI summary of insights and progress.",
        }
        return bodies.get(interaction_type, "New AI insight available. Check it out!")
