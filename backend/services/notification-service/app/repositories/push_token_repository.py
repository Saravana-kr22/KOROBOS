"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Data access layer for push notification tokens.
"""

from uuid import UUID

from app.models.model import PushToken
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class PushTokenRepository:
    """Repository for managing push notification tokens."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert(self, user_id: UUID, token: str, platform: str) -> PushToken:
        """Insert or update a push token for a user."""
        # Try to find existing token
        q = select(PushToken).where(PushToken.token == token)
        result = await self.session.execute(q)
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing record
            existing.user_id = user_id
            existing.platform = platform
            await self.session.flush()
            return existing
        else:
            # Create new token
            push_token = PushToken(user_id=user_id, token=token, platform=platform)
            self.session.add(push_token)
            await self.session.flush()
            return push_token

    async def get_by_user(self, user_id: UUID) -> list[PushToken]:
        """Get all push tokens for a user."""
        q = select(PushToken).where(PushToken.user_id == user_id)
        result = await self.session.execute(q)
        return result.scalars().all()

    async def delete(self, token: str) -> None:
        """Delete a push token."""
        q = select(PushToken).where(PushToken.token == token)
        result = await self.session.execute(q)
        push_token = result.scalar_one_or_none()
        if push_token:
            await self.session.delete(push_token)
            await self.session.flush()
