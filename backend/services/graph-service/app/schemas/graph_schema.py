"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Pydantic schemas for the Graph Service API.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class NodeResponse(BaseModel):
    """Response schema for a graph node."""

    id: UUID
    user_id: UUID
    type: str = Field(
        ...,
        description="Entity type: note|habit|learning_topic|health_log|database_record",
    )
    title: str
    source_id: UUID = Field(..., description="Original entity ID from source service")
    metadata: Optional[dict] = Field(None, description="Flexible metadata")
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EdgeResponse(BaseModel):
    """Response schema for a graph edge."""

    id: UUID
    user_id: UUID
    source_node_id: UUID
    target_node_id: UUID
    relation_type: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SubgraphResponse(BaseModel):
    """Response schema for a subgraph (nodes + edges)."""

    nodes: list[NodeResponse] = Field(default_factory=list)
    edges: list[EdgeResponse] = Field(default_factory=list)


class NeighborResponse(BaseModel):
    """Response schema for a node with its direct neighbors."""

    node: NodeResponse
    edges: list[EdgeResponse] = Field(default_factory=list)
    neighbors: list[NodeResponse] = Field(default_factory=list)


class GraphStatsResponse(BaseModel):
    """Response schema for graph statistics."""

    total_nodes: int
    total_edges: int
    node_types: dict[str, int] = Field(
        default_factory=dict, description="Count per node type"
    )
    relation_types: dict[str, int] = Field(
        default_factory=dict, description="Count per relation type"
    )


class RelatedEntitiesResponse(BaseModel):
    """Response schema for finding related entities of a specific type."""

    entity_type: str = Field(
        ...,
        description="Entity type: note|habit|learning_topic|health_log|record",
    )
    count: int
    nodes: list[NodeResponse] = Field(default_factory=list)


class KnowledgeClusterResponse(BaseModel):
    """Response schema for a single knowledge cluster."""

    cluster_id: int
    size: int
    node_ids: list[UUID]
    nodes: list[NodeResponse] = Field(default_factory=list)


class KnowledgeClustersResponse(BaseModel):
    """Response schema for all knowledge clusters."""

    total_clusters: int
    clusters: list[KnowledgeClusterResponse] = Field(default_factory=list)
