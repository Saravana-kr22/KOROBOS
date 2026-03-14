"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.
"""

from backend.shared.messaging.schemas import BaseEvent


class MetricRecordedEvent(BaseEvent):
    event_type: str = "analytics.metric.recorded"
    source_service: str = "analytics-service"
