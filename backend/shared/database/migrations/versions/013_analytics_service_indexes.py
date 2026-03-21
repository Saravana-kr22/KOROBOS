"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Analytics Service — performance indexes.

Revision ID: 013_analytics_service_indexes
Revises: 012_dashboard_streak_metric
Create Date: 2026-03-22 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "013_analytics_service_indexes"
down_revision = "012_dashboard_streak_metric"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -- Add composite index for efficient metric queries --
    op.create_index(
        "idx_analytics_metrics_user_type_date",
        "analytics_metrics",
        ["user_id", "metric_type", sa.text("created_at DESC")],
    )

    # -- Add index for user-only queries --
    op.create_index(
        "idx_analytics_metrics_user_date",
        "analytics_metrics",
        ["user_id", sa.text("created_at DESC")],
    )

    # -- Add index for metric type queries --
    op.create_index(
        "idx_analytics_metrics_type_date",
        "analytics_metrics",
        ["metric_type", sa.text("created_at DESC")],
    )


def downgrade() -> None:
    op.drop_index("idx_analytics_metrics_type_date")
    op.drop_index("idx_analytics_metrics_user_date")
    op.drop_index("idx_analytics_metrics_user_type_date")
