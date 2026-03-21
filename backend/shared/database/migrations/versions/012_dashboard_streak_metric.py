"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Dashboard Service schema extension — current streak metric.

Revision ID: 012_dashboard_streak_metric
Revises: 011_dashboard_snapshot_extended
Create Date: 2026-03-22 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "012_dashboard_streak_metric"
down_revision = "011_dashboard_snapshot_extended"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -- Add current_streak metric to daily_snapshots --
    op.add_column(
        "daily_snapshots",
        sa.Column("current_streak", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("daily_snapshots", "current_streak")
