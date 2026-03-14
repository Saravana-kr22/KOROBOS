"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.
"""

from uuid import UUID

from app.repositories.repository import NotificationRepository
from app.schemas.schema import NotificationCreate
from backend.shared.logging.logger import get_logger
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger("notification-service.logic")


class NotificationService:
    def __init__(self, session: AsyncSession):
        self.repo = NotificationRepository(session)

    async def send_notification(self, user_id: UUID, data: NotificationCreate):
        notif = await self.repo.create(
            user_id=user_id,
            title=data.title,
            body=data.body,
            channel=data.channel,
        )
        logger.info("Notification sent to user %s: %s", user_id, data.title)
        return notif

    async def list_notifications(self, user_id: UUID, offset=0, limit=50):
        return await self.repo.list_by_user(user_id, offset, limit)

    async def mark_read(self, notification_id: UUID):
        await self.repo.mark_read(notification_id)

    async def mark_all_read(self, user_id: UUID):
        await self.repo.mark_all_read(user_id)
