"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Auth business logic — registration, login, password hashing, and audit logging.
"""

from typing import Optional
from uuid import UUID

from app.events.events import UserLoginEvent, UserRegisteredEvent
from app.models.model import User
from app.repositories.repository import UserRepository
from app.schemas.schema import UserLogin, UserSignup
from backend.shared.auth.jwt_handler import create_access_token
from backend.shared.logging.audit import log_audit_event
from backend.shared.messaging.producer import publish_event
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

# bcrypt password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """Hash a plain-text password with bcrypt."""
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain-text password against its bcrypt hash."""
    return pwd_context.verify(plain, hashed)


class AuthService:
    """Core authentication business logic."""

    def __init__(self, session: AsyncSession):
        self.repo = UserRepository(session)

    async def signup(self, data: UserSignup) -> tuple[User, str]:
        """Register a new user account."""
        existing = await self.repo.get_by_email(data.email)
        if existing:
            log_audit_event(
                "auth.signup",
                action="signup",
                status="failure",
                metadata={"email": data.email, "reason": "duplicate_email"},
            )
            raise ValueError("Email already registered")

        user = await self.repo.create(
            email=data.email,
            username=data.username,
            hashed_password=hash_password(data.password),
            full_name=data.full_name or "",
        )

        token = create_access_token(
            user_id=str(user.id),
            roles=["admin"] if user.is_superuser else ["user"],
        )

        log_audit_event(
            "auth.signup",
            user_id=user.id,
            action="signup",
            status="success",
        )

        event = UserRegisteredEvent(
            payload={"user_id": str(user.id), "email": user.email}
        )
        await publish_event(event, key=str(user.id))

        return user, token

    async def login(self, data: UserLogin) -> tuple[User, str]:
        """Authenticate user and return JWT."""
        user = await self.repo.get_by_email(data.email)

        if not user or not verify_password(data.password, user.hashed_password):
            log_audit_event(
                "auth.login",
                action="login",
                status="failure",
                metadata={"email": data.email, "reason": "invalid_credentials"},
            )
            raise ValueError("Invalid email or password")

        token = create_access_token(
            user_id=str(user.id),
            roles=["admin"] if user.is_superuser else ["user"],
        )

        log_audit_event("auth.login", user_id=user.id, action="login", status="success")

        event = UserLoginEvent(payload={"user_id": str(user.id)})
        await publish_event(event, key=str(user.id))

        return user, token

    async def get_user(self, user_id: UUID) -> Optional[User]:
        return await self.repo.get_by_id(user_id)
