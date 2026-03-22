"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Kafka event definitions for the Graph Service.
"""

from backend.shared.messaging.schemas import BaseEvent


class GraphNodeCreatedEvent(BaseEvent):
    event_type: str = "graph.node.created"
    source_service: str = "graph-service"


class GraphEdgeCreatedEvent(BaseEvent):
    event_type: str = "graph.edge.created"
    source_service: str = "graph-service"
