"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Migration 006 — Create Habit Schedules table.

Adds the `habit_schedules` table to support:
- Daily, weekly, custom frequency-based scheduling
- Time-of-day reminders
- Flexible schedule engine for determining today's habits

Revision ID: 006_habit_schedules
Revises: 005_habit_service_schema_fix
Create Date: 2026-03-16 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "006_habit_schedules"
down_revision = "005_habit_service_schema_fix"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -- Habit Schedules table --
    op.create_table(
        "habit_schedules",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("habit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "frequency", sa.String(length=50), nullable=False, server_default="daily"
        ),
        sa.Column("days_of_week", sa.String(length=50), nullable=True),
        sa.Column("time_of_day", sa.Time(), nullable=True),
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
        sa.ForeignKeyConstraint(["habit_id"], ["habits.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_habit_schedules_habit_id"), "habit_schedules", ["habit_id"]
    )


def downgrade() -> None:
    # -- Restore --
    op.drop_index(op.f("ix_habit_schedules_habit_id"), "habit_schedules")
    op.drop_table("habit_schedules")
