"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Dashboard Service schema extension — notes and database metrics.

Revision ID: 011_dashboard_snapshot_extended
Revises: 010_dashboard_service_schema
Create Date: 2026-03-22 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "011_dashboard_snapshot_extended"
down_revision = "010_dashboard_service_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -- Add notes and database activity metrics to daily_snapshots --
    op.add_column(
        "daily_snapshots",
        sa.Column(
            "notes_created_today", sa.Integer(), nullable=False, server_default="0"
        ),
    )
    op.add_column(
        "daily_snapshots",
        sa.Column(
            "records_created_today", sa.Integer(), nullable=False, server_default="0"
        ),
    )


def downgrade() -> None:
    op.drop_column("daily_snapshots", "records_created_today")
    op.drop_column("daily_snapshots", "notes_created_today")
