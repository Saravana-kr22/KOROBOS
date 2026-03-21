"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Topic repository — data access for the topics table.
"""

from typing import Optional
from uuid import UUID

from app.models.topic_model import Topic
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


class TopicRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: UUID, name: str) -> Topic:
        obj = Topic(user_id=user_id, name=name)
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def get_by_id(self, topic_id: UUID) -> Optional[Topic]:
        result = await self.session.execute(select(Topic).where(Topic.id == topic_id))
        return result.scalar_one_or_none()

    async def get_by_name(self, user_id: UUID, name: str) -> Optional[Topic]:
        result = await self.session.execute(
            select(Topic).where(Topic.user_id == user_id, Topic.name == name)
        )
        return result.scalar_one_or_none()

    async def list_by_user(
        self, user_id: UUID, offset: int = 0, limit: int = 100
    ) -> tuple[list[Topic], int]:
        count_q = (
            select(func.count()).select_from(Topic).where(Topic.user_id == user_id)
        )
        total = (await self.session.execute(count_q)).scalar_one()
        q = (
            select(Topic)
            .where(Topic.user_id == user_id)
            .order_by(Topic.name.asc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(q)
        return list(result.scalars().all()), total

    async def update(self, topic: Topic, name: str) -> Topic:
        topic.name = name
        await self.session.flush()
        return topic

    async def delete(self, topic: Topic) -> None:
        await self.session.delete(topic)
        await self.session.flush()
