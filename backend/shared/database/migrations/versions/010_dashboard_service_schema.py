"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Dashboard Service schema — daily metrics snapshots.

Revision ID: 010_dashboard_service_schema
Revises: 009_health_service_schema
Create Date: 2026-03-22 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "010_dashboard_service_schema"
down_revision = "009_health_service_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -- Dashboard Service schema initialization --
    # Create daily_snapshots table for materialized aggregates of habits, health,
    # learning across a day. Used for weekly/monthly trend queries and caching.

    op.create_table(
        "daily_snapshots",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("habits_completed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_habits", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("learning_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "calories_consumed", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("calories_burned", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("net_calories", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "productivity_score", sa.Integer(), nullable=False, server_default="0"
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
    )

    # Unique constraint: one snapshot per user per date
    op.create_unique_constraint(
        "ix_daily_snapshots_user_date",
        "daily_snapshots",
        ["user_id", "snapshot_date"],
    )

    # Index for user lookups
    op.create_index(
        "ix_daily_snapshots_user_id", "daily_snapshots", ["user_id"], unique=False
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index("ix_daily_snapshots_user_id", table_name="daily_snapshots")
    op.drop_constraint(
        "ix_daily_snapshots_user_date", "daily_snapshots", type_="unique"
    )

    # Drop table
    op.drop_table("daily_snapshots")
