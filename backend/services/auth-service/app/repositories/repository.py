"""
CortexOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Data access layer for the Auth Service.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model import User


class UserRepository:
    """Repository for User CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        email: str,
        username: str,
        hashed_password: str,
        full_name: str = "",
    ) -> User:
        """Create a new user."""
        user = User(
            email=email,
            username=username,
            hashed_password=hashed_password,
            full_name=full_name,
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get a user by ID."""
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get a user by email address."""
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        """Get a user by username."""
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def update(self, user: User, **kwargs) -> User:
        """Update user fields."""
        for key, value in kwargs.items():
            if value is not None:
                setattr(user, key, value)
        await self.session.flush()
        return user

    async def deactivate(self, user: User) -> User:
        """Soft-delete by deactivating user."""
        user.is_active = False
        await self.session.flush()
        return user
