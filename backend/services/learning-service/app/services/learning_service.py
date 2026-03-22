"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.
"""

from uuid import UUID

from app.events.learning_events import (
    LearningSessionCompletedEvent,
    LearningSessionLoggedEvent,
    LearningTopicCreatedEvent,
)
from app.models.session_model import LearningSession
from app.models.topic_model import Topic
from app.repositories.session_repository import LearningRepository
from app.repositories.topic_repository import TopicRepository
from app.schemas.learning_schema import LearningSessionCreate, TopicCreate, TopicUpdate
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.messaging.producer import publish_event


class LearningService:
    def __init__(self, session: AsyncSession):
        self.repo = LearningRepository(session)
        self.topic_repo = TopicRepository(session)

    # ------------------------------------------------------------------
    # Session CRUD
    # ------------------------------------------------------------------

    async def log_session(
        self, user_id: UUID, data: LearningSessionCreate
    ) -> LearningSession:
        """Create a manually logged (completed) session."""
        if data.topic_id is not None:
            topic = await self.topic_repo.get_by_id(data.topic_id)
            if not topic or topic.user_id != user_id:
                raise HTTPException(status_code=404, detail="Topic not found")

        session = await self.repo.create(
            user_id=user_id,
            topic=data.topic,
            duration=data.duration,
            topic_id=data.topic_id,
            notes=data.notes,
            status="completed",
        )
        try:
            # Get linked notes for the session
            session_note_ids = await self.repo.get_session_note_ids(session.id)

            # Publish learning.session.completed event for knowledge graph
            if data.topic_id:
                completed_event = LearningSessionCompletedEvent(
                    payload={
                        "session_id": str(session.id),
                        "topic_id": str(data.topic_id),
                        "user_id": str(user_id),
                        "session_notes": [str(note_id) for note_id in session_note_ids],
                        "duration": data.duration,
                    }
                )
                await publish_event(completed_event, key=str(user_id))

            # Also publish session logged event for other consumers
            logged_event = LearningSessionLoggedEvent(
                payload={
                    "session_id": str(session.id),
                    "user_id": str(user_id),
                    "topic": data.topic,
                    "duration": data.duration,
                    "notes": data.notes or "",
                }
            )
            await publish_event(logged_event, key=str(user_id))
        except Exception:
            pass  # Event failure must not block session creation
        return session

    async def get_session(self, session_id: UUID) -> LearningSession | None:
        return await self.repo.get_by_id(session_id)

    async def list_sessions(
        self, user_id: UUID, offset: int = 0, limit: int = 50
    ) -> tuple[list[LearningSession], int]:
        return await self.repo.list_by_user(user_id, offset, limit)

    async def delete_session(self, session: LearningSession) -> None:
        await self.repo.delete(session)

    async def get_stats(self, user_id: UUID) -> dict:
        return await self.repo.get_stats(user_id)

    # ------------------------------------------------------------------
    # Topic CRUD
    # ------------------------------------------------------------------

    async def create_topic(self, user_id: UUID, data: TopicCreate) -> Topic:
        topic = await self.topic_repo.create(user_id=user_id, name=data.name)
        try:
            event = LearningTopicCreatedEvent(
                payload={
                    "topic_id": str(topic.id),
                    "user_id": str(user_id),
                    "name": data.name,
                }
            )
            await publish_event(event, key=str(user_id))
        except Exception:
            pass
        return topic

    async def list_topics(
        self, user_id: UUID, offset: int = 0, limit: int = 100
    ) -> tuple[list[Topic], int]:
        return await self.topic_repo.list_by_user(user_id, offset, limit)

    async def get_topic(self, topic_id: UUID) -> Topic | None:
        return await self.topic_repo.get_by_id(topic_id)

    async def update_topic(self, topic: Topic, data: TopicUpdate) -> Topic:
        return await self.topic_repo.update(topic, name=data.name)

    async def delete_topic(self, topic: Topic) -> None:
        await self.topic_repo.delete(topic)

    # ------------------------------------------------------------------
    # Note linking
    # ------------------------------------------------------------------

    async def link_note(self, session_id: UUID, note_id: UUID) -> None:
        await self.repo.link_note(session_id, note_id)

    async def unlink_note(self, session_id: UUID, note_id: UUID) -> None:
        await self.repo.unlink_note(session_id, note_id)

    async def get_session_notes(self, session_id: UUID) -> list[UUID]:
        return await self.repo.get_session_note_ids(session_id)
