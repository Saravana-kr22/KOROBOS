"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

AI Service — Learning Insight Engine.
Processes learning.session.completed events and generates AI insights.
"""

import logging
from uuid import UUID

from app.schemas.schema import AIPromptRequest
from app.services.service_logic import AIService

from backend.shared.database.connection import AsyncSessionLocal
from backend.shared.messaging.consumer import BaseEventConsumer

logger = logging.getLogger(__name__)


class LearningInsightEngine(BaseEventConsumer):
    """Consumes learning session events and generates AI insights.

    Subscribes to:
    - learning.session.completed: when a user completes a study session

    For each completed session, generates a personalized learning recommendation
    using the AI service (Gemini) with interaction_type="recommendation".

    Error Handling & DLQ:
    - Validation errors (missing fields): logged as warning, event skipped
    - Processing errors (UUID format, database, API): logged with traceback,
      re-raised to DLQ
    - BaseEventConsumer handles DLQ forwarding to {topic}.dlq with retry
      policy: [0s, 5s, 30s] delays before forwarding as BaseEvent message
    """

    topics = ["learning.session.completed"]
    group_id = "ai-service-learning"

    async def handle_event(self, topic: str, payload: dict) -> None:
        """Process learning completion event and generate recommendation.

        Args:
            topic: Event topic (learning.session.completed)
            payload: Event payload containing session_id, user_id, topic, duration, etc.
        """
        try:
            # Extract required fields
            user_id_str = payload.get("user_id")
            session_topic = payload.get("topic")
            duration = payload.get("duration")  # in minutes
            session_id = payload.get("session_id")

            if not user_id_str:
                logger.warning("Event payload missing user_id, skipping")
                return

            if not session_topic:
                logger.warning("Event payload missing topic, skipping")
                return

            if duration is None:
                logger.warning("Event payload missing duration, skipping")
                return

            user_id = UUID(user_id_str)

            # Build personalized learning prompt
            prompt = (
                f"I just completed a {duration}-minute study session on "
                f"'{session_topic}'. Based on this learning activity, what "
                f"are 3 specific next steps to deepen my understanding?"
            )

            # Create DB session and call AI service
            async with AsyncSessionLocal() as session:
                ai_svc = AIService(session)
                request = AIPromptRequest(
                    prompt=prompt,
                    interaction_type="recommendation",
                    metadata_json={"session_id": session_id, "topic": session_topic},
                )
                interaction = await ai_svc.process_prompt(user_id, request)
                await session.commit()

            logger.info(
                "Generated learning recommendation: user_id=%s, topic=%s, "
                "interaction_id=%s",
                user_id,
                session_topic,
                interaction.id,
            )

        except ValueError as e:
            logger.error("Invalid user_id format in event payload: %s", e)
        except Exception as e:
            logger.error(
                "Error processing learning event in AI insight engine: %s",
                e,
                exc_info=True,
            )
            raise
