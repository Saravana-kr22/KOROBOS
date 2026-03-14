"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

ORM models for the Auth Service.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.shared.database.base_model import Base, TimestampMixin


class User(Base, TimestampMixin):
    """Users table — stores user accounts and credentials."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(320), unique=True, nullable=False, index=True
    )
    username: Mapped[str] = mapped_column(
        String(150), unique=True, nullable=False, index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(256), nullable=False)
    full_name: Mapped[str] = mapped_column(String(300), nullable=True, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Email verification
    email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    email_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    # Account security
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    failed_login_attempts: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    account_locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    # Relationships
    sessions: Mapped[list["Session"]] = relationship(
        "Session", back_populates="user", cascade="all, delete-orphan"
    )


class Session(Base, TimestampMixin):
    """User login session tracking with refresh tokens."""

    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    refresh_token: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)
    refresh_token_hash: Mapped[str] = mapped_column(String(256), nullable=False)

    # Device information
    device_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # "mobile", "web", "tablet"
    device_name: Mapped[str | None] = mapped_column(
        String(256), nullable=True
    )  # "iPhone 15", "Chrome on Windows"
    os: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # "iOS", "Android", "Windows"
    os_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    browser: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # "Chrome", "Safari"
    browser_version: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Network information
    ip_address: Mapped[str | None] = mapped_column(
        String(45), nullable=True
    )  # IPv4 or IPv6
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Session lifecycle
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="sessions")

    # Indices for common queries
    __table_args__ = (Index("idx_user_id_created", "user_id", "created_at"),)

    def is_valid(self) -> bool:
        """Check if session is still valid."""
        now = datetime.now(timezone.utc)
        return self.revoked_at is None and now < self.expires_at

    def is_expired(self) -> bool:
        """Check if session has expired."""
        now = datetime.now(timezone.utc)
        return now >= self.expires_at

    def revoke(self) -> None:
        """Mark session as revoked (logout)."""
        self.revoked_at = datetime.now(timezone.utc)


class LoginAttemptStatus(str, Enum):
    """Login attempt status enum."""

    SUCCESS = "success"
    FAILED = "failed"
    LOCKED = "locked"


class LoginAttempt(Base):
    """Track login attempts for brute-force protection."""

    __tablename__ = "login_attempts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    ip_address: Mapped[str | None] = mapped_column(
        String(45), nullable=True, index=True
    )

    status: Mapped[LoginAttemptStatus] = mapped_column(String(20), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(256), nullable=True)

    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    __table_args__ = (
        Index("idx_email_created", "email", "created_at"),
        Index("idx_ip_created", "ip_address", "created_at"),
    )


class PasswordReset(Base):
    """Password reset token tracking."""

    __tablename__ = "password_resets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reset_token_hash: Mapped[str] = mapped_column(
        String(256), unique=True, nullable=False
    )

    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    def is_valid(self) -> bool:
        """Check if reset token is still valid."""
        now = datetime.now(timezone.utc)
        return self.used_at is None and now < self.expires_at

    def is_expired(self) -> bool:
        """Check if token has expired."""
        now = datetime.now(timezone.utc)
        return now >= self.expires_at


class EmailVerification(Base):
    """Email verification token tracking."""

    __tablename__ = "email_verifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    verification_token_hash: Mapped[str] = mapped_column(
        String(256), unique=True, nullable=False
    )

    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    def is_valid(self) -> bool:
        """Check if verification token is still valid."""
        now = datetime.now(timezone.utc)
        return self.verified_at is None and now < self.expires_at

    def is_expired(self) -> bool:
        """Check if token has expired."""
        now = datetime.now(timezone.utc)
        return now >= self.expires_at
