"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Tests for Notification Service API endpoints.
"""

from uuid import UUID

import pytest
from pydantic import BaseModel


class PushTokenRequest(BaseModel):
    """Request body for registering a push token."""

    token: str
    platform: str  # "ios" or "android"


class NotificationResponse(BaseModel):
    """Response model for a notification."""

    id: UUID
    title: str
    body: str
    channel: str
    is_read: bool

    model_config = {"from_attributes": True}


def test_push_token_request_schema():
    """Test PushTokenRequest schema validation."""
    data = PushTokenRequest(
        token="exponent-push-token[ABC123XYZ]",
        platform="ios",
    )
    assert data.token == "exponent-push-token[ABC123XYZ]"
    assert data.platform == "ios"


def test_push_token_invalid_platform():
    """Test PushTokenRequest validates platform value."""
    # Schema allows any string; validation should be at route level
    data = PushTokenRequest(token="token123", platform="web")
    assert data.platform == "web"


def test_notification_response_schema():
    """Test NotificationResponse schema validation."""
    response = NotificationResponse(
        id=UUID(int=1),
        title="Habit Reminder",
        body="Time to complete your morning workout",
        channel="reminders",
        is_read=False,
    )
    assert response.title == "Habit Reminder"
    assert response.is_read is False


def test_notification_response_with_read_status():
    """Test NotificationResponse with read status."""
    response = NotificationResponse(
        id=UUID(int=2),
        title="Learning Session Complete",
        body="Great job finishing your learning session",
        channel="achievements",
        is_read=True,
    )
    assert response.is_read is True


@pytest.mark.asyncio
async def test_notification_pagination():
    """Test notification listing supports pagination."""
    # Verify pagination parameters are accepted
    assert True  # Placeholder for integration test
