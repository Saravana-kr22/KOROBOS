"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

AI Service — Habit Insight Engine.
Processes habit.completed events and generates AI insights.
"""

import logging
from uuid import UUID

from app.schemas.schema import AIPromptRequest
from app.services.service_logic import AIService

from backend.shared.database.connection import async_session_factory
from backend.shared.messaging.consumer import BaseEventConsumer

logger = logging.getLogger(__name__)


class HabitInsightEngine(BaseEventConsumer):
    """Consumes habit completion events and generates AI insights.

    Subscribes to:
    - habit.completed: when a user completes a habit

    For each completed habit, generates a personalized habit recommendation
    using the AI service (Gemini) with interaction_type="recommendation".
    """

    topics = ["habit.completed"]
    group_id = "ai-service-habit"

    async def handle_event(self, topic: str, payload: dict) -> None:
        """Process habit completion event and generate recommendation.

        Args:
            topic: Event topic (habit.completed)
            payload: Event payload containing habit_id, user_id, name, streak, etc.
        """
        try:
            # Extract required fields
            user_id_str = payload.get("user_id")
            habit_name = payload.get("name")
            streak = payload.get("streak", 1)
            habit_id = payload.get("habit_id")

            if not user_id_str:
                logger.warning("Event payload missing user_id, skipping")
                return

            if not habit_name:
                logger.warning("Event payload missing habit name, skipping")
                return

            user_id = UUID(user_id_str)

            # Build personalized habit prompt
            prompt = (
                f"I just completed my habit '{habit_name}' with a streak of "
                f"{streak} days. What are 3 ways I can sustain or strengthen "
                f"this habit?"
            )

            # Create DB session and call AI service
            async with async_session_factory() as session:
                ai_svc = AIService(session)
                request = AIPromptRequest(
                    prompt=prompt,
                    interaction_type="recommendation",
                    metadata_json={
                        "habit_id": habit_id,
                        "habit_name": habit_name,
                        "streak": streak,
                    },
                )
                interaction = await ai_svc.process_prompt(user_id, request)
                await session.commit()

            logger.info(
                "Generated habit recommendation: user_id=%s, habit=%s, "
                "streak=%s, interaction_id=%s",
                user_id,
                habit_name,
                streak,
                interaction.id,
            )

        except ValueError as e:
            logger.error("Invalid user_id format in event payload: %s", e)
        except Exception as e:
            logger.error(
                "Error processing habit event in AI insight engine: %s",
                e,
                exc_info=True,
            )
            raise
