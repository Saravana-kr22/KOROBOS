"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.
"""

from uuid import UUID

from app.events.events import LearningSessionLoggedEvent
from app.repositories.repository import LearningRepository
from app.schemas.schema import LearningSessionCreate
from backend.shared.messaging.producer import publish_event
from sqlalchemy.ext.asyncio import AsyncSession


class LearningService:
    def __init__(self, session: AsyncSession):
        self.repo = LearningRepository(session)

    async def log_session(self, user_id: UUID, data: LearningSessionCreate):
        session = await self.repo.create(
            user_id=user_id,
            topic=data.topic,
            duration=data.duration,
            notes=data.notes or "",
        )
        event = LearningSessionLoggedEvent(
            payload={
                "session_id": str(session.id),
                "user_id": str(user_id),
                "topic": data.topic,
                "duration": data.duration,
                "notes": data.notes or "",
            }
        )
        await publish_event(event, key=str(user_id))
        return session

    async def get_session(self, session_id: UUID):
        return await self.repo.get_by_id(session_id)

    async def list_sessions(self, user_id: UUID, offset: int = 0, limit: int = 50):
        return await self.repo.list_by_user(user_id, offset, limit)

    async def get_stats(self, user_id: UUID):
        return await self.repo.get_stats(user_id)

    async def delete_session(self, session):
        await self.repo.delete(session)
