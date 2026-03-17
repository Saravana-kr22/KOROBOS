"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Notification Service API routes — push tokens and in-app notifications.
"""

from uuid import UUID

from app.repositories.push_token_repository import PushTokenRepository
from app.repositories.repository import NotificationRepository
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.database.connection import get_db_session

router = APIRouter()


def _get_user_id(x_user_id: str = Header(..., alias="X-User-ID")) -> UUID:
    """Extract user ID from X-User-ID header."""
    return UUID(x_user_id)


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


class NotificationListResponse(BaseModel):
    """Response model for listing notifications."""

    notifications: list[NotificationResponse]
    total: int


@router.get("/")
async def root():
    return {"service": "notification-service", "status": "running"}


@router.post("/notifications/push-token", status_code=201, tags=["Notifications"])
async def register_push_token(
    data: PushTokenRequest,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """Register or update a push token for the authenticated user."""
    repo = PushTokenRepository(session)
    push_token = await repo.upsert(user_id, data.token, data.platform)
    await session.commit()
    return {
        "id": str(push_token.id),
        "token": push_token.token,
        "platform": push_token.platform,
    }


@router.get(
    "/notifications", response_model=NotificationListResponse, tags=["Notifications"]
)
async def list_notifications(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """Get all notifications for the authenticated user."""
    repo = NotificationRepository(session)
    notifications, total, unread = await repo.list_by_user(user_id, offset, limit)
    return {"notifications": notifications, "total": total}


@router.put("/notifications/{notification_id}/read", tags=["Notifications"])
async def mark_notification_read(
    notification_id: UUID,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """Mark a notification as read."""
    repo = NotificationRepository(session)
    notification = await repo.get_by_id(notification_id)
    if not notification or notification.user_id != user_id:
        raise HTTPException(status_code=404, detail="Notification not found")
    notification.is_read = True
    await session.flush()
    await session.commit()
    return {"id": str(notification.id), "is_read": notification.is_read}
