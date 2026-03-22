"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

AI Service schema — insights and recommendations.

Revision ID: 015_ai_insights_recommendations
Revises: 014_graph_service_schema
Create Date: 2026-03-22 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "015_ai_insights_recommendations"
down_revision = "014_graph_service_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -- AI Service: Insights --
    op.create_table(
        "ai_insights",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "insight_type",
            sa.String(length=50),
            nullable=False,
            comment="behavioral, performance, health, knowledge",
        ),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column(
            "confidence",
            sa.Float(),
            nullable=False,
            server_default="1.0",
            comment="0.0 to 1.0",
        ),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'{}'::jsonb"),
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
    )

    # Indexes for common queries
    op.create_index(
        "idx_ai_insights_user_id",
        "ai_insights",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "idx_ai_insights_user_type",
        "ai_insights",
        ["user_id", "insight_type"],
        unique=False,
    )
    op.create_index(
        "idx_ai_insights_created_at",
        "ai_insights",
        ["created_at"],
        unique=False,
    )

    # -- AI Service: Recommendations --
    op.create_table(
        "ai_recommendations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "category",
            sa.String(length=50),
            nullable=False,
            comment="habit, learning, health, productivity",
        ),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column(
            "priority",
            sa.String(length=20),
            nullable=False,
            server_default="medium",
            comment="high, medium, low",
        ),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'{}'::jsonb"),
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
    )

    # Indexes for common queries
    op.create_index(
        "idx_ai_recommendations_user_id",
        "ai_recommendations",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "idx_ai_recommendations_user_category",
        "ai_recommendations",
        ["user_id", "category"],
        unique=False,
    )
    op.create_index(
        "idx_ai_recommendations_priority",
        "ai_recommendations",
        ["priority"],
        unique=False,
    )
    op.create_index(
        "idx_ai_recommendations_created_at",
        "ai_recommendations",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index("idx_ai_recommendations_created_at")
    op.drop_index("idx_ai_recommendations_priority")
    op.drop_index("idx_ai_recommendations_user_category")
    op.drop_index("idx_ai_recommendations_user_id")
    op.drop_index("idx_ai_insights_created_at")
    op.drop_index("idx_ai_insights_user_type")
    op.drop_index("idx_ai_insights_user_id")

    # Drop tables
    op.drop_table("ai_recommendations")
    op.drop_table("ai_insights")
