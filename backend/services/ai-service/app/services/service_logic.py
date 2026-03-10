"""
CortexOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.
"""

from uuid import UUID

from app.events.events import AIInteractionCompletedEvent
from app.repositories.repository import AIRepository
from app.schemas.schema import AIPromptRequest
from backend.shared.messaging.producer import publish_event
from sqlalchemy.ext.asyncio import AsyncSession


class AIService:
    def __init__(self, session: AsyncSession):
        self.repo = AIRepository(session)

    async def process_prompt(self, user_id: UUID, data: AIPromptRequest):
        """Create an AI interaction record and process the prompt."""
        interaction = await self.repo.create(
            user_id=user_id,
            interaction_type=data.interaction_type,
            prompt=data.prompt,
            metadata_json=data.metadata_json,
        )

        # TODO: Integrate with LLM provider (OpenAI, Gemini, etc.)
        response_text = (
            f"[AI Response Placeholder] Processed {data.interaction_type} request."
        )

        interaction = await self.repo.update_response(interaction, response_text)

        event = AIInteractionCompletedEvent(
            payload={
                "interaction_id": str(interaction.id),
                "user_id": str(user_id),
                "type": data.interaction_type,
            }
        )
        await publish_event(event, key=str(user_id))

        return interaction

    async def get_interaction(self, interaction_id: UUID):
        return await self.repo.get_by_id(interaction_id)

    async def list_interactions(self, user_id: UUID, offset=0, limit=50):
        return await self.repo.list_by_user(user_id, offset, limit)
