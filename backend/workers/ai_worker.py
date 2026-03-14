"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

AI Worker

Consumes domain events and records placeholder AI interactions in the AI
service database so Sprint 4 has a concrete AI insight trigger pipeline.
"""

import asyncio
import importlib
from typing import Any
from uuid import UUID

from backend.shared.database.connection import async_session_factory
from backend.shared.logging.logger import get_logger
from backend.shared.messaging.consumer import BaseEventConsumer
from backend.shared.messaging.schemas import BaseEvent
from backend.workers.event_transforms import ai_prompt_for_event
from backend.workers.service_loader import configure_service_app_path
from backend.workers.topics import AI_TOPICS

configure_service_app_path("ai-service")
AIPromptRequest = importlib.import_module("app.schemas.schema").AIPromptRequest
AIService = importlib.import_module("app.services.service_logic").AIService

logger = get_logger("ai-worker")


class AIEventConsumer(BaseEventConsumer):
    """Consumer that translates activity events into AI insight jobs."""

    async def handle_event(self, topic: str, payload: dict[str, Any]):
        event = BaseEvent.model_validate(payload)
        data = event.payload

        user_id_raw = data.get("user_id")
        if not user_id_raw:
            logger.warning("Skipping AI event without user_id: %s", event.event_type)
            return

        prompt_kwargs = ai_prompt_for_event(event.event_type, data)
        if prompt_kwargs is None:
            logger.debug("Ignoring non-AI event_type: %s", event.event_type)
            return

        async with async_session_factory() as session:
            service = AIService(session)
            await service.process_prompt(
                UUID(user_id_raw),
                AIPromptRequest(**prompt_kwargs),
            )
            await session.commit()


async def main() -> None:
    consumer = AIEventConsumer(
        topics=list(AI_TOPICS),
        group_id="ai-group",
    )
    await consumer.start()

    logger.info("AI worker started")
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("AI worker shutting down")
        await consumer.stop()


if __name__ == "__main__":
    asyncio.run(main())
