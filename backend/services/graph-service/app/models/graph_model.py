"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

ORM models for the Graph Service.
"""

import uuid

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.shared.database.base_model import Base, TimestampMixin


class GraphNode(Base, TimestampMixin):
    """Graph nodes — entities in the knowledge graph."""

    __tablename__ = "graph_nodes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Entity type: note|habit|learning_topic|health_log|database_record",
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="Original entity ID from source service",
    )
    metadata_json: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, default=None
    )

    # Relationships
    outgoing_edges: Mapped[list["GraphEdge"]] = relationship(
        foreign_keys="GraphEdge.source_node_id",
        back_populates="source_node",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<GraphNode id={self.id} type={self.type} title={self.title}>"


class GraphEdge(Base, TimestampMixin):
    """Graph edges — relationships between nodes."""

    __tablename__ = "graph_edges"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    source_node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("graph_nodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("graph_nodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    relation_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Relationship type: note_links|habit_related_to_learning|...",
    )

    # Relationships
    source_node: Mapped[GraphNode] = relationship(
        foreign_keys=[source_node_id], back_populates="outgoing_edges"
    )
    target_node: Mapped[GraphNode] = relationship(
        foreign_keys=[target_node_id],
    )

    def __repr__(self) -> str:
        src = self.source_node_id
        tgt = self.target_node_id
        return f"<GraphEdge {src} --{self.relation_type}--> {tgt}>"
