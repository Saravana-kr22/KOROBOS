"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class NotificationCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    body: str = Field(default="")
    channel: str = Field(default="in_app", description="in_app, email, push")


class NotificationResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    body: str
    channel: str
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    notifications: list[NotificationResponse]
    total: int
    unread: int
