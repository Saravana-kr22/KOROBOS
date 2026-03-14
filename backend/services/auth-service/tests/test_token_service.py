"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Unit tests for TokenService token and session management.
"""


import pytest
from app.models.model import Session, User
from app.services.token_service import TokenService
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.auth.jwt_handler import verify_refresh_token, verify_token


@pytest.mark.asyncio
class TestTokenServiceCreateTokens:
    """Tests for token creation."""

    async def test_create_tokens_returns_both_tokens(self, test_db: AsyncSession):
        """Test create_tokens returns access and refresh tokens."""
        # Create test user
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed",
            email_verified=True,
        )
        test_db.add(user)
        await test_db.flush()

        token_svc = TokenService(test_db)
        tokens = await token_svc.create_tokens(user.id, roles=["user"])

        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"
        assert tokens["expires_in"] == 15 * 60  # 15 minutes
        assert tokens["refresh_expires_in"] == 30 * 24 * 60 * 60  # 30 days

    async def test_create_tokens_access_token_valid(self, test_db: AsyncSession):
        """Test created access token is valid."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed",
            email_verified=True,
        )
        test_db.add(user)
        await test_db.flush()

        token_svc = TokenService(test_db)
        tokens = await token_svc.create_tokens(user.id, roles=["user"])

        # Verify token
        payload = verify_token(tokens["access_token"])
        assert payload["sub"] == str(user.id)
        assert payload["roles"] == ["user"]

    async def test_create_tokens_refresh_token_valid(self, test_db: AsyncSession):
        """Test created refresh token is valid."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed",
            email_verified=True,
        )
        test_db.add(user)
        await test_db.flush()

        token_svc = TokenService(test_db)
        tokens = await token_svc.create_tokens(user.id, roles=["user"])

        # Verify refresh token
        payload = verify_refresh_token(tokens["refresh_token"])
        assert payload["sub"] == str(user.id)
        assert payload["token_type"] == "refresh"

    async def test_create_tokens_creates_session(self, test_db: AsyncSession):
        """Test create_tokens creates a session record."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed",
            email_verified=True,
        )
        test_db.add(user)
        await test_db.flush()

        token_svc = TokenService(test_db)
        await token_svc.create_tokens(
            user.id,
            roles=["user"],
            device_info={"type": "mobile", "os": "iOS"},
            ip_address="192.168.1.1",
        )
        await test_db.flush()

        # Check session created
        from sqlalchemy import select

        result = await test_db.execute(
            select(Session).where(Session.user_id == user.id)
        )
        session = result.scalar_one_or_none()

        assert session is not None
        assert session.device_type == "mobile"
        assert session.os == "iOS"
        assert session.ip_address == "192.168.1.1"


@pytest.mark.asyncio
class TestTokenServiceRefresh:
    """Tests for token refresh."""

    async def test_refresh_access_token_success(self, test_db: AsyncSession):
        """Test successful token refresh."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed",
            is_active=True,
            email_verified=True,
        )
        test_db.add(user)
        await test_db.flush()

        token_svc = TokenService(test_db)

        # Create initial tokens
        tokens = await token_svc.create_tokens(user.id, roles=["user"])
        await test_db.commit()

        # Refresh the token
        new_tokens = await token_svc.refresh_access_token(tokens["refresh_token"])

        assert "access_token" in new_tokens
        assert new_tokens["token_type"] == "bearer"

    async def test_refresh_invalid_token_fails(self, test_db: AsyncSession):
        """Test refresh with invalid token fails."""
        token_svc = TokenService(test_db)

        with pytest.raises(ValueError, match="Invalid"):
            await token_svc.refresh_access_token("invalid_token")

    async def test_refresh_revoked_session_fails(self, test_db: AsyncSession):
        """Test refresh with revoked session fails."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed",
            is_active=True,
            email_verified=True,
        )
        test_db.add(user)
        await test_db.flush()

        token_svc = TokenService(test_db)

        # Create tokens
        tokens = await token_svc.create_tokens(user.id, roles=["user"])
        await test_db.commit()

        # Revoke the session
        await token_svc.revoke_session(user.id, refresh_token=tokens["refresh_token"])
        await test_db.commit()

        # Refresh should fail
        with pytest.raises(ValueError, match="invalid"):
            await token_svc.refresh_access_token(tokens["refresh_token"])

    async def test_refresh_inactive_user_fails(self, test_db: AsyncSession):
        """Test refresh fails for inactive user."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed",
            is_active=False,
            email_verified=True,
        )
        test_db.add(user)
        await test_db.flush()

        token_svc = TokenService(test_db)

        # Create tokens
        tokens = await token_svc.create_tokens(user.id, roles=["user"])
        await test_db.commit()

        # Deactivate user
        user.is_active = False
        test_db.add(user)
        await test_db.commit()

        # Refresh should fail
        with pytest.raises(ValueError, match="not found"):
            await token_svc.refresh_access_token(tokens["refresh_token"])


@pytest.mark.asyncio
class TestTokenServiceRevoke:
    """Tests for session revocation."""

    async def test_revoke_specific_session(self, test_db: AsyncSession):
        """Test revoking a specific session."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed",
            email_verified=True,
        )
        test_db.add(user)
        await test_db.flush()

        token_svc = TokenService(test_db)

        # Create two sessions
        tokens1 = await token_svc.create_tokens(user.id, roles=["user"])
        tokens2 = await token_svc.create_tokens(user.id, roles=["user"])
        await test_db.commit()

        # Revoke first session
        await token_svc.revoke_session(user.id, refresh_token=tokens1["refresh_token"])
        await test_db.commit()

        # First session should fail refresh
        with pytest.raises(ValueError):
            await token_svc.refresh_access_token(tokens1["refresh_token"])

        # Second session should still work
        new_tokens = await token_svc.refresh_access_token(tokens2["refresh_token"])
        assert "access_token" in new_tokens

    async def test_revoke_all_sessions(self, test_db: AsyncSession):
        """Test revoking all sessions."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed",
            email_verified=True,
        )
        test_db.add(user)
        await test_db.flush()

        token_svc = TokenService(test_db)

        # Create two sessions
        tokens1 = await token_svc.create_tokens(user.id, roles=["user"])
        tokens2 = await token_svc.create_tokens(user.id, roles=["user"])
        await test_db.commit()

        # Revoke all sessions
        await token_svc.revoke_session(user.id)
        await test_db.commit()

        # Both should fail refresh
        with pytest.raises(ValueError):
            await token_svc.refresh_access_token(tokens1["refresh_token"])

        with pytest.raises(ValueError):
            await token_svc.refresh_access_token(tokens2["refresh_token"])


@pytest.mark.asyncio
class TestTokenServiceGetSessions:
    """Tests for getting active sessions."""

    async def test_get_active_sessions(self, test_db: AsyncSession):
        """Test retrieving active sessions."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed",
            email_verified=True,
        )
        test_db.add(user)
        await test_db.flush()

        token_svc = TokenService(test_db)

        # Create two sessions
        await token_svc.create_tokens(
            user.id, roles=["user"], device_info={"type": "web"}
        )
        await token_svc.create_tokens(
            user.id, roles=["user"], device_info={"type": "mobile"}
        )
        await test_db.commit()

        # Get sessions
        sessions = await token_svc.get_active_sessions(user.id)

        assert len(sessions) == 2
        assert sessions[0].device_type in ["web", "mobile"]
        assert sessions[1].device_type in ["web", "mobile"]

    async def test_get_sessions_excludes_revoked(self, test_db: AsyncSession):
        """Test that revoked sessions are excluded."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed",
            email_verified=True,
        )
        test_db.add(user)
        await test_db.flush()

        token_svc = TokenService(test_db)

        # Create two sessions
        tokens1 = await token_svc.create_tokens(user.id, roles=["user"])
        await token_svc.create_tokens(user.id, roles=["user"])
        await test_db.commit()

        # Revoke first
        await token_svc.revoke_session(user.id, refresh_token=tokens1["refresh_token"])
        await test_db.commit()

        # Get sessions should only return active
        sessions = await token_svc.get_active_sessions(user.id)
        assert len(sessions) == 1
