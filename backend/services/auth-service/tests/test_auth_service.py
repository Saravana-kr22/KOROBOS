"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Unit tests for AuthService business logic.
"""

import pytest
from app.models.model import EmailVerification
from app.schemas.schema import UserLogin, UserSignup
from app.services.service_logic import AuthService, hash_password, verify_password
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
class TestAuthServiceSignup:
    """Tests for user signup."""

    async def test_signup_creates_user(
        self, test_db: AsyncSession, test_user_data: dict
    ):
        """Test successful user creation."""
        svc = AuthService(test_db)
        signup_data = UserSignup(**test_user_data)

        user, token = await svc.signup(signup_data)

        assert user.email == test_user_data["email"]
        assert user.username == test_user_data["username"]
        assert user.full_name == test_user_data["full_name"]
        assert not user.email_verified
        assert token  # Access token returned

    async def test_signup_hashes_password(
        self, test_db: AsyncSession, test_user_data: dict
    ):
        """Test password is properly hashed."""
        svc = AuthService(test_db)
        signup_data = UserSignup(**test_user_data)

        user, _ = await svc.signup(signup_data)
        await test_db.refresh(user)

        # Password should be hashed, not plaintext
        assert user.hashed_password != test_user_data["password"]
        assert verify_password(test_user_data["password"], user.hashed_password)

    async def test_signup_duplicate_email_fails(
        self, test_db: AsyncSession, test_user_data: dict
    ):
        """Test signup with duplicate email fails."""
        svc = AuthService(test_db)
        signup_data = UserSignup(**test_user_data)

        # First signup succeeds
        await svc.signup(signup_data)
        await test_db.commit()

        # Second signup fails
        with pytest.raises(ValueError, match="already registered"):
            await svc.signup(signup_data)

    async def test_signup_weak_password_fails(
        self, test_db: AsyncSession, test_user_data: dict
    ):
        """Test weak password is rejected."""
        test_user_data["password"] = "weak"
        with pytest.raises(ValidationError):
            UserSignup(**test_user_data)

    async def test_signup_invalid_email_fails(
        self, test_db: AsyncSession, test_user_data: dict
    ):
        """Test invalid email is rejected."""
        svc = AuthService(test_db)
        test_user_data["email"] = "not-an-email"
        signup_data = UserSignup(**test_user_data)

        with pytest.raises(ValueError, match="email"):
            await svc.signup(signup_data)

    async def test_signup_creates_email_verification_token(
        self, test_db: AsyncSession, test_user_data: dict
    ):
        """Test email verification token is created."""
        svc = AuthService(test_db)
        signup_data = UserSignup(**test_user_data)

        user, _ = await svc.signup(signup_data)
        await test_db.commit()

        # Check verification token exists
        from sqlalchemy import select

        result = await test_db.execute(
            select(EmailVerification).where(EmailVerification.user_id == user.id)
        )
        verification = result.scalar_one_or_none()

        assert verification is not None
        assert verification.email == test_user_data["email"]
        assert verification.verified_at is None


@pytest.mark.asyncio
class TestAuthServiceLogin:
    """Tests for user login."""

    async def test_login_requires_email_verification(
        self, test_db: AsyncSession, test_user_data: dict, test_login_data: dict
    ):
        """Test login fails if email not verified."""
        svc = AuthService(test_db)

        # Create user
        signup_data = UserSignup(**test_user_data)
        await svc.signup(signup_data)
        await test_db.commit()

        # Try to login
        login_data = UserLogin(**test_login_data)
        with pytest.raises(ValueError, match="not verified"):
            await svc.login(login_data)

    async def test_login_success_with_verified_email(
        self, test_db: AsyncSession, test_user_data: dict, test_login_data: dict
    ):
        """Test successful login with verified email."""
        from datetime import datetime, timezone

        svc = AuthService(test_db)

        # Create and verify user
        signup_data = UserSignup(**test_user_data)
        user, _ = await svc.signup(signup_data)
        user.email_verified = True
        user.email_verified_at = datetime.now(timezone.utc)
        test_db.add(user)
        await test_db.commit()

        # Login should succeed
        login_data = UserLogin(**test_login_data)
        logged_in_user, token = await svc.login(login_data)

        assert logged_in_user.id == user.id
        assert token

    async def test_login_invalid_password_fails(
        self, test_db: AsyncSession, test_user_data: dict
    ):
        """Test login with wrong password fails."""
        from datetime import datetime, timezone

        svc = AuthService(test_db)

        # Create verified user
        signup_data = UserSignup(**test_user_data)
        user, _ = await svc.signup(signup_data)
        user.email_verified = True
        user.email_verified_at = datetime.now(timezone.utc)
        test_db.add(user)
        await test_db.commit()

        # Login with wrong password
        login_data = UserLogin(
            email=test_user_data["email"], password="WrongPassword123!"
        )
        with pytest.raises(ValueError, match="Invalid"):
            await svc.login(login_data)

    async def test_login_tracks_failed_attempts(
        self, test_db: AsyncSession, test_user_data: dict
    ):
        """Test failed login attempts are tracked."""
        from datetime import datetime, timezone

        svc = AuthService(test_db)

        # Create verified user
        signup_data = UserSignup(**test_user_data)
        user, _ = await svc.signup(signup_data)
        user.email_verified = True
        user.email_verified_at = datetime.now(timezone.utc)
        test_db.add(user)
        await test_db.commit()

        # Make failed attempts
        login_data = UserLogin(
            email=test_user_data["email"], password="WrongPassword123!"
        )

        for i in range(3):
            with pytest.raises(ValueError):
                await svc.login(login_data)

        # Check failed attempts incremented
        await test_db.refresh(user)
        assert user.failed_login_attempts == 3

    async def test_login_locks_account_after_max_attempts(
        self, test_db: AsyncSession, test_user_data: dict
    ):
        """Test account locks after max failed attempts."""
        from datetime import datetime, timezone

        svc = AuthService(test_db)

        # Create verified user
        signup_data = UserSignup(**test_user_data)
        user, _ = await svc.signup(signup_data)
        user.email_verified = True
        user.email_verified_at = datetime.now(timezone.utc)
        test_db.add(user)
        await test_db.commit()

        # Make 5 failed attempts
        login_data = UserLogin(
            email=test_user_data["email"], password="WrongPassword123!"
        )

        for _ in range(5):
            with pytest.raises(ValueError):
                await svc.login(login_data)

        # Check account is locked
        await test_db.refresh(user)
        assert user.account_locked_until is not None
        assert user.failed_login_attempts == 5

    async def test_login_fails_when_account_locked(
        self, test_db: AsyncSession, test_user_data: dict
    ):
        """Test login fails when account is locked."""
        from datetime import datetime, timedelta, timezone

        svc = AuthService(test_db)

        # Create locked account
        signup_data = UserSignup(**test_user_data)
        user, _ = await svc.signup(signup_data)
        user.email_verified = True
        user.email_verified_at = datetime.now(timezone.utc)
        user.account_locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)
        test_db.add(user)
        await test_db.commit()

        # Login should fail
        login_data = UserLogin(**test_user_data)
        with pytest.raises(ValueError, match="locked"):
            await svc.login(login_data)

    async def test_login_resets_failed_attempts_on_success(
        self, test_db: AsyncSession, test_user_data: dict, test_login_data: dict
    ):
        """Test failed login counter resets on successful login."""
        from datetime import datetime, timezone

        svc = AuthService(test_db)

        # Create user with failed attempts
        signup_data = UserSignup(**test_user_data)
        user, _ = await svc.signup(signup_data)
        user.email_verified = True
        user.email_verified_at = datetime.now(timezone.utc)
        user.failed_login_attempts = 3
        test_db.add(user)
        await test_db.commit()

        # Login succeeds
        login_data = UserLogin(**test_login_data)
        await svc.login(login_data)
        await test_db.commit()

        # Check counter reset
        await test_db.refresh(user)
        assert user.failed_login_attempts == 0


@pytest.mark.asyncio
class TestEmailVerification:
    """Tests for email verification."""

    async def test_verify_email_success(
        self, test_db: AsyncSession, test_user_data: dict
    ):
        """Test successful email verification."""
        import hashlib

        svc = AuthService(test_db)

        # Create user
        signup_data = UserSignup(**test_user_data)
        user, _ = await svc.signup(signup_data)
        await test_db.commit()

        # Get verification token
        from sqlalchemy import select

        result = await test_db.execute(
            select(EmailVerification).where(EmailVerification.user_id == user.id)
        )
        verification = result.scalar_one_or_none()

        # Create a new token to verify (simulate email link click)
        test_token = "test_verification_token"
        verification.verification_token_hash = hashlib.sha256(
            test_token.encode()
        ).hexdigest()
        test_db.add(verification)
        await test_db.commit()

        # Verify email
        verified_user = await svc.verify_email(test_token)
        assert verified_user.email_verified
        assert verified_user.email_verified_at is not None

    async def test_verify_email_invalid_token_fails(self, test_db: AsyncSession):
        """Test verification with invalid token fails."""
        svc = AuthService(test_db)

        with pytest.raises(ValueError, match="invalid"):
            await svc.verify_email("invalid_token")

    async def test_verify_email_expired_token_fails(
        self, test_db: AsyncSession, test_user_data: dict
    ):
        """Test verification with expired token fails."""
        from datetime import datetime, timedelta, timezone

        svc = AuthService(test_db)

        # Create user with expired verification token
        signup_data = UserSignup(**test_user_data)
        user, _ = await svc.signup(signup_data)
        await test_db.commit()

        # Expire the token
        from sqlalchemy import select

        result = await test_db.execute(
            select(EmailVerification).where(EmailVerification.user_id == user.id)
        )
        verification = result.scalar_one_or_none()
        verification.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        test_db.add(verification)
        await test_db.commit()

        test_token = "any_token"
        with pytest.raises(ValueError, match="expired"):
            await svc.verify_email(test_token)


@pytest.mark.asyncio
class TestPasswordReset:
    """Tests for password reset."""

    async def test_request_password_reset(
        self, test_db: AsyncSession, test_user_data: dict
    ):
        """Test password reset request creates token."""
        svc = AuthService(test_db)

        # Create user
        signup_data = UserSignup(**test_user_data)
        user, _ = await svc.signup(signup_data)
        await test_db.commit()

        # Request reset
        reset = await svc.request_password_reset(test_user_data["email"])

        assert reset is not None
        assert reset.user_id == user.id
        assert reset.used_at is None

    async def test_reset_password_success(
        self, test_db: AsyncSession, test_user_data: dict
    ):
        """Test successful password reset."""
        import hashlib

        svc = AuthService(test_db)

        # Create user
        signup_data = UserSignup(**test_user_data)
        user, _ = await svc.signup(signup_data)
        await test_db.commit()

        # Request reset
        reset = await svc.request_password_reset(test_user_data["email"])
        original_password_hash = user.hashed_password

        # Create test reset token
        test_token = "test_reset_token"
        reset.reset_token_hash = hashlib.sha256(test_token.encode()).hexdigest()
        test_db.add(reset)
        await test_db.commit()

        # Reset password
        new_password = "NewPassword123!"
        updated_user = await svc.reset_password(test_token, new_password)

        assert updated_user.hashed_password != original_password_hash
        assert verify_password(new_password, updated_user.hashed_password)

    async def test_reset_password_weak_password_fails(
        self, test_db: AsyncSession, test_user_data: dict
    ):
        """Test reset with weak password fails."""
        svc = AuthService(test_db)

        # Create user and request reset
        signup_data = UserSignup(**test_user_data)
        await svc.signup(signup_data)
        await test_db.commit()

        with pytest.raises(ValueError, match="password"):
            await svc.reset_password("any_token", "weak")

    async def test_reset_password_invalid_token_fails(self, test_db: AsyncSession):
        """Test reset with invalid token fails."""
        svc = AuthService(test_db)

        with pytest.raises(ValueError, match="invalid"):
            await svc.reset_password("invalid_token", "NewPassword123!")


@pytest.mark.asyncio
class TestPasswordHashing:
    """Tests for password hashing."""

    def test_hash_password(self):
        """Test password hashing."""
        password = "TestPassword123!"
        hashed = hash_password(password)

        assert hashed != password
        assert len(hashed) > len(password)

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "TestPassword123!"
        hashed = hash_password(password)

        assert verify_password(password, hashed)

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "TestPassword123!"
        hashed = hash_password(password)

        assert not verify_password("WrongPassword123!", hashed)

    def test_hashed_passwords_are_different(self):
        """Test same password hashed twice produces different hashes."""
        password = "TestPassword123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # Hashes should be different (due to salt)
        assert hash1 != hash2
        # But both should verify
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)
