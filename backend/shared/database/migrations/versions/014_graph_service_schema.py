"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Graph Service schema — knowledge graph nodes and edges.

Revision ID: 014_graph_service_schema
Revises: 013_analytics_service_indexes
Create Date: 2026-03-22 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "014_graph_service_schema"
down_revision = "013_analytics_service_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -- Graph Service: Nodes (Entities) --
    op.create_table(
        "graph_nodes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "type",
            sa.String(length=50),
            nullable=False,
            comment="Entity type: note|habit|learning_topic|health_log|database_record",
        ),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column(
            "source_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="Original entity ID from source service",
        ),
        sa.Column(
            "metadata",
            postgresql.JSON(),
            nullable=True,
            comment="Flexible metadata storage",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "source_id", name="uq_graph_nodes_user_source"),
    )

    # Indexes for common queries
    op.create_index(
        "idx_graph_nodes_user_type",
        "graph_nodes",
        ["user_id", "type"],
        unique=False,
    )
    op.create_index(
        "idx_graph_nodes_user_id",
        "graph_nodes",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "idx_graph_nodes_source_id",
        "graph_nodes",
        ["source_id"],
        unique=False,
    )

    # -- Graph Service: Edges (Relationships) --
    op.create_table(
        "graph_edges",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "source_node_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "target_node_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "relation_type",
            sa.String(length=100),
            nullable=False,
            comment="Relationship type: note_links|habit_related_to_learning|...",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["source_node_id"],
            ["graph_nodes.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["target_node_id"],
            ["graph_nodes.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Indexes for efficient graph traversal
    op.create_index(
        "idx_graph_edges_source_node",
        "graph_edges",
        ["source_node_id"],
        unique=False,
    )
    op.create_index(
        "idx_graph_edges_target_node",
        "graph_edges",
        ["target_node_id"],
        unique=False,
    )
    op.create_index(
        "idx_graph_edges_user_id",
        "graph_edges",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "idx_graph_edges_relation_type",
        "graph_edges",
        ["relation_type"],
        unique=False,
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index("idx_graph_edges_relation_type", table_name="graph_edges")
    op.drop_index("idx_graph_edges_user_id", table_name="graph_edges")
    op.drop_index("idx_graph_edges_target_node", table_name="graph_edges")
    op.drop_index("idx_graph_edges_source_node", table_name="graph_edges")
    op.drop_index("idx_graph_nodes_source_id", table_name="graph_nodes")
    op.drop_index("idx_graph_nodes_user_id", table_name="graph_nodes")
    op.drop_index("idx_graph_nodes_user_type", table_name="graph_nodes")

    # Drop tables
    op.drop_table("graph_edges")
    op.drop_table("graph_nodes")
