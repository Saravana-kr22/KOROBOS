"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Auth business logic — registration, login, password hashing, and audit logging.
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

import bcrypt
from app.events.events import UserLoginEvent, UserRegisteredEvent
from app.models.model import EmailVerification, LoginAttempt, PasswordReset, User
from app.repositories.repository import UserRepository
from app.schemas.schema import UserLogin, UserSignup
from app.services.email_service import (
    send_password_reset_email,
    send_verification_email,
)
from app.services.metrics import increment_metric
from app.utils.validation import EmailValidator, PasswordValidator
from passlib.context import CryptContext
from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.auth.jwt_handler import create_access_token
from backend.shared.logging.audit import log_audit_event
from backend.shared.logging.logger import get_logger
from backend.shared.messaging.producer import publish_event

# -- Passlib/Bcrypt 4.0+ Compatibility Patch --
# Passlib 1.7.4 is incompatible with bcrypt 4.0+ because bcrypt now raises
# ValueError for passwords > 72 bytes, while passlib's internal health check
# uses a 255-byte secret. We monkey-patch bcrypt to truncate silently.
_original_hashpw = bcrypt.hashpw


def _patched_hashpw(password, salt):
    if isinstance(password, str):
        password = password.encode("utf-8")
    return _original_hashpw(password[:72], salt)


bcrypt.hashpw = _patched_hashpw
# ---------------------------------------------

logger = get_logger("auth-service.auth")

# bcrypt password context
pwd_context = CryptContext(
    schemes=["bcrypt"], deprecated="auto", bcrypt__truncate_error=False
)


def hash_password(plain: str) -> str:
    """Hash a plain-text password with bcrypt."""
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain-text password against its bcrypt hash."""
    return pwd_context.verify(plain, hashed)


class AuthService:
    """Core authentication business logic."""

    MAX_LOGIN_ATTEMPTS = 5
    LOGIN_ATTEMPT_WINDOW = timedelta(minutes=15)
    LOCKOUT_DURATION = timedelta(minutes=30)

    def __init__(self, session: AsyncSession):
        self.repo = UserRepository(session)
        self.session = session

    async def signup(self, data: UserSignup) -> tuple[User, str]:
        """
        Register a new user account.

        Args:
            data: UserSignup schema with email, password, username, full_name.

        Returns:
            Tuple of (User, access_token).

        Raises:
            ValueError: If email already registered or validation fails.
        """
        # Validate email format
        if not EmailValidator.validate(data.email):
            increment_metric("signup_failure")
            increment_metric("signup_invalid_email")
            log_audit_event(
                "auth.signup",
                action="signup",
                status="failure",
                metadata={"email": data.email, "reason": "invalid_email"},
            )
            raise ValueError("Invalid email format")

        # Validate password strength
        is_valid, message = PasswordValidator.validate(data.password)
        if not is_valid:
            increment_metric("signup_failure")
            increment_metric("signup_weak_password")
            log_audit_event(
                "auth.signup",
                action="signup",
                status="failure",
                metadata={"email": data.email, "reason": "weak_password"},
            )
            raise ValueError(f"Password too weak: {message}")

        existing = await self.repo.get_by_email(data.email)
        if existing:
            increment_metric("signup_failure")
            increment_metric("signup_duplicate_email")
            log_audit_event(
                "auth.signup",
                action="signup",
                status="failure",
                metadata={"email": data.email, "reason": "duplicate_email"},
            )
            raise ValueError(
                f"Registration failed: User with email {data.email} "
                "is already registered (duplicate email)"
            )

        user = await self.repo.create(
            email=data.email,
            username=data.username,
            hashed_password=hash_password(data.password),
            full_name=data.full_name or "",
            email_verified=False,
        )

        # Create email verification token
        verification_token = secrets.token_urlsafe(32)
        verification_hash = hashlib.sha256(verification_token.encode()).hexdigest()

        verification = EmailVerification(
            user_id=user.id,
            email=data.email,
            verification_token_hash=verification_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        )
        self.session.add(verification)
        await self.session.flush()

        token = create_access_token(
            user_id=str(user.id),
            email=user.email,
            roles=["admin"] if user.is_superuser else ["user"],
        )

        increment_metric("signup_success")
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

        # Send verification email in background (don't block on email)
        try:
            await send_verification_email(
                email=user.email,
                verification_token=verification_token,
                username=user.full_name or user.username,
            )
        except Exception as exc:
            logger.error(f"Failed to send verification email: {exc}")
            # Continue anyway - user can request email resend

        return user, token

    async def login(
        self,
        data: UserLogin,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> tuple[User, str]:
        """
        Authenticate user and return JWT.

        Args:
            data: UserLogin schema with email, password.
            ip_address: Optional client IP address.
            user_agent: Optional client user agent.

        Returns:
            Tuple of (User, access_token).

        Raises:
            ValueError: If credentials invalid, account locked, or email not verified.
        """
        email = data.email.lower()
        user = await self.repo.get_by_email(email)

        # Check if account is locked
        if user and user.account_locked_until:
            if datetime.now(timezone.utc) < user.account_locked_until:
                increment_metric("login_failure")
                increment_metric("login_account_locked")
                lockout_metadata = {
                    "email": email,
                    "reason": "account_locked",
                    "ip": ip_address,
                }
                log_audit_event(
                    "auth.login",
                    user_id=str(user.id),
                    action="login",
                    status="failure",
                    metadata=lockout_metadata,
                )
                raise ValueError("Account locked. Try again later.")

            # Unlock if lockout duration expired
            user.account_locked_until = None
            self.session.add(user)

        # Verify password
        if not user or not verify_password(data.password, user.hashed_password):
            increment_metric("login_failure")
            increment_metric("login_invalid_credentials")

            # Record failed attempt
            await self._record_login_attempt(
                email=email,
                ip_address=ip_address,
                status="failed",
                reason="invalid_credentials",
            )

            if user:
                user.failed_login_attempts += 1

                # Lock account if max attempts exceeded
                if user.failed_login_attempts >= self.MAX_LOGIN_ATTEMPTS:
                    increment_metric("account_lockout")
                    user.account_locked_until = (
                        datetime.now(timezone.utc) + self.LOCKOUT_DURATION
                    )
                    log_audit_event(
                        "auth.login",
                        user_id=str(user.id),
                        action="login",
                        status="failure",
                        metadata={
                            "reason": "account_locked",
                            "failed_attempts": user.failed_login_attempts,
                        },
                    )

                self.session.add(user)
                await self.session.flush()

            cred_metadata = {
                "email": email,
                "reason": "invalid_credentials",
                "ip": ip_address,
            }
            log_audit_event(
                "auth.login",
                user_id=str(user.id) if user else None,
                action="login",
                status="failure",
                metadata=cred_metadata,
            )
            raise ValueError("Invalid email or password")

        # Verify email is verified
        if not user.email_verified:
            increment_metric("login_failure")
            increment_metric("login_email_not_verified")
            log_audit_event(
                "auth.login",
                user_id=str(user.id),
                action="login",
                status="failure",
                metadata={"reason": "email_not_verified"},
            )
            raise ValueError("Email not verified")

        if not user.is_active:
            increment_metric("login_failure")
            increment_metric("login_account_inactive")
            log_audit_event(
                "auth.login",
                user_id=str(user.id),
                action="login",
                status="failure",
                metadata={"reason": "account_inactive"},
            )
            raise ValueError("User account is inactive")

        # Reset failed attempts on successful login
        user.failed_login_attempts = 0
        user.last_login_at = datetime.now(timezone.utc)
        self.session.add(user)

        # Record successful login attempt
        await self._record_login_attempt(
            email=email,
            ip_address=ip_address,
            status="success",
        )

        token = create_access_token(
            user_id=str(user.id),
            email=user.email,
            roles=["admin"] if user.is_superuser else ["user"],
        )

        increment_metric("login_success")
        log_audit_event(
            "auth.login",
            user_id=user.id,
            action="login",
            status="success",
            metadata={"ip": ip_address},
        )

        event = UserLoginEvent(payload={"user_id": str(user.id)})
        await publish_event(event, key=str(user.id))

        return user, token

    async def verify_email(self, token: str) -> User:
        """
        Verify user email with token.

        Args:
            token: Email verification token.

        Returns:
            Verified User object.

        Raises:
            ValueError: If token is invalid or expired.
        """
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        stmt = select(EmailVerification).where(
            EmailVerification.verification_token_hash == token_hash
        )
        result = await self.session.execute(stmt)
        verification = result.scalar_one_or_none()

        if not verification or verification.is_expired():
            increment_metric("email_verification_failure")
            increment_metric("email_verification_invalid_token")
            raise ValueError("Verification token invalid or expired")

        user = await self.session.get(User, verification.user_id)
        user.email_verified = True
        user.email_verified_at = datetime.now(timezone.utc)

        verification.verified_at = datetime.now(timezone.utc)

        self.session.add(user)
        self.session.add(verification)

        increment_metric("email_verification_success")
        log_audit_event(
            "auth.email_verified",
            user_id=str(user.id),
            action="email_verified",
            status="success",
        )

        return user

    async def request_password_reset(self, email: str) -> Optional[PasswordReset]:
        """
        Request password reset token.

        Args:
            email: User email address.

        Returns:
            PasswordReset object if user exists, None otherwise.
            Note: Always returns success to prevent email enumeration.
        """
        user = await self.repo.get_by_email(email.lower())

        if user:
            increment_metric("password_reset_requested")
            reset_token = secrets.token_urlsafe(32)
            reset_hash = hashlib.sha256(reset_token.encode()).hexdigest()

            # Invalidate previous reset tokens
            stmt = delete(PasswordReset).where(
                and_(
                    PasswordReset.user_id == user.id,
                    PasswordReset.used_at.is_(None),
                )
            )
            await self.session.execute(stmt)

            reset = PasswordReset(
                user_id=user.id,
                reset_token_hash=reset_hash,
                expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            )
            self.session.add(reset)
            await self.session.flush()

            log_audit_event(
                "auth.password_reset_requested",
                user_id=str(user.id),
                action="password_reset_requested",
                status="success",
            )

            # Send reset email in background (don't block on email)
            try:
                await send_password_reset_email(
                    email=user.email,
                    reset_token=reset_token,
                    username=user.full_name or user.username,
                )
            except Exception as exc:
                logger.error(f"Failed to send password reset email: {exc}")
                # Continue anyway - prevent email enumeration

            return reset

        return None

    async def reset_password(self, token: str, new_password: str) -> User:
        """
        Reset user password with token.

        Args:
            token: Password reset token.
            new_password: New plain-text password.

        Returns:
            User object with updated password.

        Raises:
            ValueError: If token invalid, expired, or password too weak.
        """
        # Validate new password
        is_valid, message = PasswordValidator.validate(new_password)
        if not is_valid:
            increment_metric("password_reset_failure")
            raise ValueError(f"New password too weak: {message}")

        token_hash = hashlib.sha256(token.encode()).hexdigest()

        stmt = select(PasswordReset).where(PasswordReset.reset_token_hash == token_hash)
        result = await self.session.execute(stmt)
        reset = result.scalar_one_or_none()

        if not reset or not reset.is_valid():
            increment_metric("password_reset_failure")
            increment_metric("password_reset_invalid_token")
            raise ValueError("Reset token invalid or expired")

        user = await self.session.get(User, reset.user_id)
        user.hashed_password = hash_password(new_password)
        user.failed_login_attempts = 0
        user.account_locked_until = None

        reset.used_at = datetime.now(timezone.utc)

        self.session.add(user)
        self.session.add(reset)

        increment_metric("password_reset_success")
        log_audit_event(
            "auth.password_reset",
            user_id=str(user.id),
            action="password_reset",
            status="success",
        )

        return user

    async def _record_login_attempt(
        self,
        email: str,
        ip_address: Optional[str] = None,
        status: str = "failed",
        reason: Optional[str] = None,
    ) -> None:
        """
        Record login attempt for analytics and security tracking.

        Args:
            email: User email.
            ip_address: Client IP.
            status: "success", "failed", or "locked".
            reason: Optional failure reason.
        """
        attempt = LoginAttempt(
            email=email,
            ip_address=ip_address,
            status=status,
            reason=reason,
        )
        self.session.add(attempt)
        await self.session.flush()

    async def resend_verification_email(self, email: str) -> None:
        """
        Resend email verification email to user.

        Args:
            email: User's email address.

        Raises:
            ValueError: If user not found or already verified.
        """
        user = await self.repo.get_by_email(email)

        if not user:
            increment_metric("email_verification_resend_requested")
            # Don't reveal if email exists (security)
            return

        if user.email_verified:
            increment_metric("email_verification_resend_requested")
            # Already verified, silently succeed
            return

        # Create new verification token
        verification_token = secrets.token_urlsafe(32)
        verification_hash = hashlib.sha256(verification_token.encode()).hexdigest()

        # Invalidate old verification tokens
        stmt = delete(EmailVerification).where(EmailVerification.user_id == user.id)
        await self.session.execute(stmt)

        # Create new verification record
        verification = EmailVerification(
            user_id=user.id,
            email=user.email,
            verification_token_hash=verification_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        )
        self.session.add(verification)
        await self.session.flush()

        increment_metric("email_verification_resend_requested")
        log_audit_event(
            "auth.email_resend",
            user_id=user.id,
            action="email_resend",
            status="success",
        )

        # Send verification email in background
        try:
            await send_verification_email(
                email=user.email,
                verification_token=verification_token,
                username=user.full_name or user.username,
            )
        except Exception as exc:
            logger.error(f"Failed to send verification email resend: {exc}")
            # Continue anyway

    async def unlock_account(self, user_id: UUID) -> User:
        """
        Unlock a locked account (admin action).

        Args:
            user_id: User to unlock.

        Returns:
            Updated User object.

        Raises:
            ValueError: If user not found.
        """
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        if user.account_locked_until:
            increment_metric("account_unlock")
            user.account_locked_until = None
            user.failed_login_attempts = 0
            self.session.add(user)

            log_audit_event(
                "auth.account_unlock",
                user_id=user.id,
                action="account_unlock",
                status="success",
            )

        return user

    async def request_account_unlock(self, email: str) -> None:
        """
        Request account unlock via email token (self-service).

        Args:
            email: User's email address.

        Returns:
            None - always returns success to prevent email enumeration.
        """
        user = await self.repo.get_by_email(email)

        if not user or not user.account_locked_until:
            # User doesn't exist or not locked; silently succeed
            return

        # Create unlock token
        unlock_token = secrets.token_urlsafe(32)
        unlock_hash = hashlib.sha256(unlock_token.encode()).hexdigest()

        # For now, we'll use PasswordReset table with a special marker
        # In production, create a dedicated UnlockRequest table
        unlock = PasswordReset(
            user_id=user.id,
            reset_token_hash=unlock_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        self.session.add(unlock)
        await self.session.flush()

        log_audit_event(
            "auth.account_unlock_requested",
            user_id=user.id,
            action="account_unlock_requested",
            status="success",
        )

        # Send unlock email in background
        try:
            unlock_url_base = "https://app.korobos.com"

            from app.services.email_service import send_password_reset_email

            # Reuse password reset email template with different message
            await send_password_reset_email(
                email=user.email,
                reset_token=unlock_token,
                username=user.full_name or user.username,
                reset_url_base=unlock_url_base,
            )
        except Exception as exc:
            logger.error(f"Failed to send unlock email: {exc}")
            # Continue anyway

    async def confirm_account_unlock(self, token: str) -> User:
        """
        Confirm account unlock with token.

        Args:
            token: Unlock token from email.

        Returns:
            Updated User object.

        Raises:
            ValueError: If token invalid or expired.
        """
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        stmt = select(PasswordReset).where(PasswordReset.reset_token_hash == token_hash)
        result = await self.session.execute(stmt)
        unlock = result.scalar_one_or_none()

        if not unlock or not unlock.is_valid():
            raise ValueError("Unlock token invalid or expired")

        user = await self.session.get(User, unlock.user_id)
        if not user:
            raise ValueError("User not found")

        # Unlock account
        increment_metric("account_unlock")
        user.account_locked_until = None
        user.failed_login_attempts = 0

        unlock.used_at = datetime.now(timezone.utc)

        self.session.add(user)
        self.session.add(unlock)

        log_audit_event(
            "auth.account_unlocked",
            user_id=user.id,
            action="account_unlocked",
            status="success",
        )

        return user

    async def get_user(self, user_id: UUID) -> Optional[User]:
        return await self.repo.get_by_id(user_id)
