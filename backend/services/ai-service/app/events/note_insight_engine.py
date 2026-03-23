"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

AI Service — Note Insight Engine.
Processes note.created events and generates AI insights.
"""

import logging
from uuid import UUID

from app.schemas.schema import AIPromptRequest
from app.services.service_logic import AIService

from backend.shared.database.connection import async_session_factory
from backend.shared.messaging.consumer import BaseEventConsumer

logger = logging.getLogger(__name__)


class NoteInsightEngine(BaseEventConsumer):
    """Consumes note creation events and generates AI insights.

    Subscribes to:
    - note.created: when a user creates a note

    For each created note, generates a personalized knowledge insight
    using the AI service (Gemini) with interaction_type="summary".
    """

    topics = ["note.created"]
    group_id = "ai-service-notes"

    async def handle_event(self, topic: str, payload: dict) -> None:
        """Process note creation event and generate insight.

        Args:
            topic: Event topic (note.created)
            payload: Event payload containing note_id, user_id, title, content,
                tags, etc.
        """
        try:
            # Extract required fields
            user_id_str = payload.get("user_id")
            note_title = payload.get("title")
            note_content = payload.get("content", "")
            tags = payload.get("tags", [])
            note_id = payload.get("note_id")

            if not user_id_str:
                logger.warning("Event payload missing user_id, skipping")
                return

            if not note_title:
                logger.warning("Event payload missing note title, skipping")
                return

            user_id = UUID(user_id_str)

            # Truncate content for prompt (avoid token limits)
            content_snippet = note_content[:200] if note_content else "(no content)"

            # Build personalized note insight prompt
            tag_str = ", ".join(tags) if tags else "none"
            prompt = (
                f"I just created a note titled '{note_title}' with content: "
                f"{content_snippet}... Tags: {tag_str}. What key insights or "
                f"next learning steps would you recommend based on this?"
            )

            # Create DB session and call AI service
            async with async_session_factory() as session:
                ai_svc = AIService(session)
                request = AIPromptRequest(
                    prompt=prompt,
                    interaction_type="summary",
                    metadata_json={
                        "note_id": note_id,
                        "note_title": note_title,
                        "tags": tags,
                    },
                )
                interaction = await ai_svc.process_prompt(user_id, request)
                await session.commit()

            logger.info(
                "Generated note insight: user_id=%s, title=%s, " "interaction_id=%s",
                user_id,
                note_title,
                interaction.id,
            )

        except ValueError as e:
            logger.error("Invalid user_id format in event payload: %s", e)
        except Exception as e:
            logger.error(
                "Error processing note event in AI insight engine: %s",
                e,
                exc_info=True,
            )
            raise
