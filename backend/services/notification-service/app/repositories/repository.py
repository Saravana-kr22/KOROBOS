"""
CortexOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model import Notification


class NotificationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: UUID, title: str, body: str, channel: str = "in_app") -> Notification:
        obj = Notification(user_id=user_id, title=title, body=body, channel=channel)
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def list_by_user(self, user_id: UUID, offset: int = 0, limit: int = 50) -> tuple[list[Notification], int, int]:
        total = (await self.session.execute(select(func.count()).select_from(Notification).where(Notification.user_id == user_id))).scalar_one()
        unread = (await self.session.execute(select(func.count()).select_from(Notification).where(Notification.user_id == user_id, Notification.is_read.is_(False)))).scalar_one()
        q = select(Notification).where(Notification.user_id == user_id).order_by(Notification.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(q)
        return list(result.scalars().all()), total, unread

    async def mark_read(self, notification_id: UUID) -> None:
        stmt = update(Notification).where(Notification.id == notification_id).values(is_read=True)
        await self.session.execute(stmt)
        await self.session.flush()

    async def mark_all_read(self, user_id: UUID) -> None:
        stmt = update(Notification).where(Notification.user_id == user_id, Notification.is_read.is_(False)).values(is_read=True)
        await self.session.execute(stmt)
        await self.session.flush()
