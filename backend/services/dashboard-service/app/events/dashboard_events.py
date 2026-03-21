"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Dashboard Service events.
"""

from backend.shared.events.base_event import BaseEvent


class DashboardUpdatedEvent(BaseEvent):
    """
    Emitted when dashboard metrics are computed and persisted.

    Payload includes productivity score, habits completed, learning minutes,
    and calories balance for downstream AI insights and analytics.
    """

    event_type: str = "dashboard.updated"
    source_service: str = "dashboard-service"
