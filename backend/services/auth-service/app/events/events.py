"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Kafka event definitions for the Auth Service.
"""

from backend.shared.messaging.schemas import BaseEvent


class UserRegisteredEvent(BaseEvent):
    """Event emitted when a new user registers."""

    event_type: str = "user.registered"
    source_service: str = "auth-service"


class UserLoginEvent(BaseEvent):
    """Event emitted when a user logs in."""

    event_type: str = "user.login"
    source_service: str = "auth-service"
