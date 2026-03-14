"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Token service — manages token creation, validation, and session tracking.
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from app.models.model import Session, User
from app.services.metrics import increment_metric
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.auth.jwt_handler import create_access_token, verify_refresh_token


class TokenService:
    """Manage token generation, validation, and refresh."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_tokens(
        self,
        user_id: UUID,
        email: str,
        roles: list[str] | None = None,
        device_info: dict | None = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> dict:
        """
        Create access + refresh token pair with session tracking.

        Args:
            user_id: User identifier.
            email: User's email address.
            roles: User roles for JWT.
            device_info: Optional device metadata dict with keys: type, name, os,
                os_version, browser, browser_version.
            ip_address: Client IP address.
            user_agent: Client user agent string.

        Returns:
            Dict with access_token, refresh_token, token_type, expires_in,
            refresh_expires_in.
        """
        # Generate tokens
        access_token = create_access_token(str(user_id), email=email, roles=roles)

        # Generate refresh token securely
        refresh_token_raw = secrets.token_urlsafe(32)
        refresh_token_hash = self._hash_token(refresh_token_raw)

        # Create session record
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)

        session = Session(
            user_id=user_id,
            refresh_token=refresh_token_raw,
            refresh_token_hash=refresh_token_hash,
            device_type=device_info.get("type") if device_info else None,
            device_name=device_info.get("name") if device_info else None,
            os=device_info.get("os") if device_info else None,
            os_version=device_info.get("os_version") if device_info else None,
            browser=device_info.get("browser") if device_info else None,
            browser_version=device_info.get("browser_version") if device_info else None,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at,
        )
        self.session.add(session)
        await self.session.flush()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token_raw,
            "token_type": "bearer",
            "expires_in": 15 * 60,  # 15 minutes in seconds
            "refresh_expires_in": 30 * 24 * 60 * 60,  # 30 days in seconds
        }

    async def refresh_access_token(self, refresh_token: str) -> dict:
        """
        Generate new access token from refresh token.

        Args:
            refresh_token: Refresh token string.

        Returns:
            Dict with new access_token, token_type, expires_in.

        Raises:
            ValueError: If token is invalid or session is revoked.
        """
        try:
            payload = verify_refresh_token(refresh_token)
        except ValueError as exc:
            increment_metric("token_refresh_failure")
            increment_metric("token_refresh_invalid_token")
            raise ValueError(f"Invalid refresh token: {exc}") from exc

        user_id = UUID(payload["sub"])

        # Verify session exists and is valid
        stmt = select(Session).where(
            and_(
                Session.refresh_token == refresh_token,
                Session.user_id == user_id,
                Session.revoked_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        session = result.scalar_one_or_none()

        if not session or not session.is_valid():
            increment_metric("token_refresh_failure")
            raise ValueError("Session invalid or expired")

        # Get user to fetch current roles and email
        user = await self.session.get(User, user_id)
        if not user or not user.is_active:
            increment_metric("token_refresh_failure")
            raise ValueError("User not found or inactive")

        # Generate new access token
        roles = ["admin"] if user.is_superuser else ["user"]
        access_token = create_access_token(str(user_id), email=user.email, roles=roles)

        # Update session activity
        session.last_activity_at = datetime.now(timezone.utc)
        self.session.add(session)

        increment_metric("token_refresh_success")
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 15 * 60,
        }

    async def revoke_session(
        self,
        user_id: UUID,
        refresh_token: Optional[str] = None,
    ) -> None:
        """
        Revoke a user session (logout).

        Args:
            user_id: User identifier.
            refresh_token: Optional specific refresh token. If None,
                revokes all sessions.
        """
        if refresh_token:
            # Revoke specific session
            stmt = select(Session).where(
                and_(
                    Session.refresh_token == refresh_token,
                    Session.user_id == user_id,
                )
            )
            result = await self.session.execute(stmt)
            session = result.scalar_one_or_none()
            if session:
                session.revoke()
                self.session.add(session)
        else:
            # Revoke all active sessions
            stmt = select(Session).where(
                and_(
                    Session.user_id == user_id,
                    Session.revoked_at.is_(None),
                )
            )
            result = await self.session.execute(stmt)
            sessions = result.scalars().all()
            for sess in sessions:
                sess.revoke()
                self.session.add(sess)

    async def get_active_sessions(self, user_id: UUID) -> list[Session]:
        """
        Get all active sessions for a user.

        Args:
            user_id: User identifier.

        Returns:
            List of active Session objects.
        """
        stmt = (
            select(Session)
            .where(
                and_(
                    Session.user_id == user_id,
                    Session.revoked_at.is_(None),
                )
            )
            .order_by(Session.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    @staticmethod
    def _hash_token(token: str) -> str:
        """Hash token for secure storage."""
        return hashlib.sha256(token.encode()).hexdigest()
