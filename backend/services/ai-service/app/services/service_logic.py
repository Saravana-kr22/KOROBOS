"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.
"""

import asyncio
import logging
from uuid import UUID

from app.events.events import AIInteractionCompletedEvent
from app.repositories.repository import AIRepository
from app.schemas.schema import AIPromptRequest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.config.settings import get_settings
from backend.shared.messaging.producer import publish_event

logger = logging.getLogger(__name__)

_SYSTEM_PROMPTS = {
    "summary": (
        "You are a concise knowledge assistant. "
        "Summarize the given note in 2–3 sentences and list up to 3 key takeaways."
    ),
    "recommendation": (
        "You are an expert learning coach. "
        "Analyze the user's study topics and duration. "
        "Suggest 3 concrete next steps, identify potential knowledge gaps, "
        "and suggest the most productive times for future study based on their history."
    ),
    "gap_analysis": (
        "You are a learning gap analyst. "
        "Analyze the user's learning history to identify gaps. "
        "For the given topic, identify: 1) concepts likely missed or "
        "underexplored, 2) weak prerequisite knowledge, "
        "3) areas to revisit for deeper understanding. Be actionable."
    ),
    "study_optimization": (
        "You are a study optimization coach. "
        "Based on the user's study patterns (session frequency, duration, topics), "
        "suggest optimal study strategies including: "
        "1) ideal session length and frequency for this topic, "
        "2) spaced repetition schedule recommendations, "
        "3) complementary topics to study alongside. "
        "Ground suggestions in evidence-based learning science."
    ),
    "assistant": "You are a helpful assistant. Answer the user's question clearly.",
}


def _call_gemini(prompt: str, interaction_type: str) -> str:
    """Call the Google Gemini API synchronously and return the response text.

    Uses the free-tier gemini-2.0-flash model by default.
    Falls back to a labelled placeholder when GEMINI_API_KEY is not set so the
    service starts cleanly in development without credentials.

    Get a free API key at https://aistudio.google.com
    """
    settings = get_settings()
    if not settings.gemini_api_key:
        logger.warning(
            "GEMINI_API_KEY not set — returning placeholder for %s interaction",
            interaction_type,
        )
        return (
            f"[AI placeholder — set GEMINI_API_KEY to enable real responses] "
            f"Interaction type: {interaction_type}."
        )

    import google.generativeai as genai  # lazy: only needed when key is set

    genai.configure(api_key=settings.gemini_api_key)
    system_prompt = _SYSTEM_PROMPTS.get(interaction_type, _SYSTEM_PROMPTS["assistant"])

    model = genai.GenerativeModel(
        model_name=settings.gemini_model,
        system_instruction=system_prompt,
        generation_config=genai.GenerationConfig(
            max_output_tokens=settings.gemini_max_tokens,
        ),
    )
    response = model.generate_content(prompt)
    return response.text


class AIService:
    def __init__(self, session: AsyncSession):
        self.repo = AIRepository(session)

    async def process_prompt(self, user_id: UUID, data: AIPromptRequest):
        """Create an AI interaction record, call Gemini, and persist the response."""
        interaction = await self.repo.create(
            user_id=user_id,
            interaction_type=data.interaction_type,
            prompt=data.prompt,
            metadata_json=data.metadata_json,
        )

        response_text = await asyncio.to_thread(
            _call_gemini, data.prompt, data.interaction_type
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
