"""
CortexOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.
"""

from typing import Optional
from uuid import UUID

from app.models.model import LearningSession
from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession


class LearningRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: UUID,
        topic: str,
        duration: int,
        notes: str = "",
    ) -> LearningSession:
        obj = LearningSession(
            user_id=user_id,
            topic=topic,
            duration=duration,
            notes=notes,
        )
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def get_by_id(self, session_id: UUID) -> Optional[LearningSession]:
        result = await self.session.execute(
            select(LearningSession).where(LearningSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        user_id: UUID,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[LearningSession], int]:
        count_q = (
            select(func.count())
            .select_from(LearningSession)
            .where(LearningSession.user_id == user_id)
        )
        total = (await self.session.execute(count_q)).scalar_one()
        q = (
            select(LearningSession)
            .where(LearningSession.user_id == user_id)
            .order_by(LearningSession.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(q)
        return list(result.scalars().all()), total

    async def delete(self, obj: LearningSession) -> None:
        await self.session.delete(obj)
        await self.session.flush()

    async def get_stats(self, user_id: UUID) -> dict:
        total_q = (
            select(func.count())
            .select_from(LearningSession)
            .where(LearningSession.user_id == user_id)
        )
        minutes_q = select(func.coalesce(func.sum(LearningSession.duration), 0)).where(
            LearningSession.user_id == user_id
        )
        topics_q = select(distinct(LearningSession.topic)).where(
            LearningSession.user_id == user_id
        )

        total = (await self.session.execute(total_q)).scalar_one()
        minutes = (await self.session.execute(minutes_q)).scalar_one()
        topics = [r for r in (await self.session.execute(topics_q)).scalars().all()]

        return {"total_sessions": total, "total_minutes": minutes, "topics": topics}
