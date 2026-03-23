"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

AI Service — Health Insight Engine.
Processes meal.logged and workout.logged events and generates AI insights.
"""

import logging
from uuid import UUID

from app.schemas.schema import AIPromptRequest
from app.services.service_logic import AIService

from backend.shared.database.connection import async_session_factory
from backend.shared.messaging.consumer import BaseEventConsumer

logger = logging.getLogger(__name__)


class HealthInsightEngine(BaseEventConsumer):
    """Consumes health-related events and generates AI insights.

    Subscribes to:
    - meal.logged: when a user logs a meal
    - workout.logged: when a user logs a workout

    For each health event, generates a personalized health recommendation
    using the AI service (Gemini) with interaction_type="recommendation".
    """

    topics = ["meal.logged", "workout.logged"]
    group_id = "ai-service-health"

    async def handle_event(self, topic: str, payload: dict) -> None:
        """Process health event and generate recommendation.

        Args:
            topic: Event topic (meal.logged or workout.logged)
            payload: Event payload containing user_id, food_name/workout_type,
                calories, etc.
        """
        try:
            # Extract required fields
            user_id_str = payload.get("user_id")

            if not user_id_str:
                logger.warning("Event payload missing user_id, skipping")
                return

            user_id = UUID(user_id_str)

            # Handle meal.logged events
            if topic == "meal.logged":
                food_name = payload.get("food_name", "food")
                calories = payload.get("calories", 0)
                protein = payload.get("protein")

                prompt = (
                    f"I just logged a meal of '{food_name}' with {calories} calories "
                    f"and {protein}g protein. What are 2 tips to balance my nutrition?"
                )
                metadata = {
                    "log_type": "meal",
                    "food_name": food_name,
                    "calories": calories,
                }

            # Handle workout.logged events
            elif topic == "workout.logged":
                workout_type = payload.get("workout_type", "exercise")
                duration = payload.get("duration", 0)
                calories_burned = payload.get("calories", 0)

                prompt = (
                    f"I just completed a {duration}-minute {workout_type} workout "
                    f"and burned {calories_burned} calories. How can I improve "
                    f"my fitness routine?"
                )
                metadata = {
                    "log_type": "workout",
                    "workout_type": workout_type,
                    "duration": duration,
                }

            else:
                logger.warning(f"Unknown topic in health insight engine: {topic}")
                return

            # Create DB session and call AI service
            async with async_session_factory() as session:
                ai_svc = AIService(session)
                request = AIPromptRequest(
                    prompt=prompt,
                    interaction_type="recommendation",
                    metadata_json=metadata,
                )
                interaction = await ai_svc.process_prompt(user_id, request)
                await session.commit()

            logger.info(
                "Generated health recommendation: user_id=%s, topic=%s, "
                "interaction_id=%s",
                user_id,
                topic,
                interaction.id,
            )

        except ValueError as e:
            logger.error("Invalid user_id format in event payload: %s", e)
        except Exception as e:
            logger.error(
                "Error processing health event in AI insight engine: %s",
                e,
                exc_info=True,
            )
            raise
