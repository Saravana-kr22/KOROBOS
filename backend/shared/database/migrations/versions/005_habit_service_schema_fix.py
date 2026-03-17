"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Migration 005 — Fix Habit Service schema to match current ORM design.

The 001_initial migration created habits with current_streak, longest_streak,
and last_completed columns, and habit_logs with only completed_at. The current ORM
redesigned this: removed streak tracking columns, added log_date (Date) and
completed (Boolean), and added is_active flag per Sprint 8 requirements.

This migration aligns the database schema to the current ORM models.

Revision ID: 005_habit_service_schema_fix
Revises: 004_database_service
Create Date: 2026-03-16 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

revision = "005_habit_service_schema_fix"
down_revision = "004_database_service"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -- Fix habits table --
    # 1. Alter name column from String(200) to String(300) per ORM
    op.alter_column(
        "habits",
        "name",
        existing_type=sa.String(length=200),
        type_=sa.String(length=300),
    )

    # 2. Add is_active column (per Sprint 8 spec)
    op.add_column(
        "habits",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
    )

    # 3. Drop streak-tracking columns
    op.drop_column("habits", "current_streak")
    op.drop_column("habits", "longest_streak")
    op.drop_column("habits", "last_completed")

    # 4. Create index on user_id (ORM has index=True)
    op.create_index(op.f("ix_habits_user_id"), "habits", ["user_id"])

    # -- Fix habit_logs table --
    # 5. Drop completed_at column
    op.drop_column("habit_logs", "completed_at")

    # 6. Add log_date (Date) column per ORM
    op.add_column(
        "habit_logs",
        sa.Column(
            "log_date",
            sa.Date(),
            nullable=False,
            server_default=sa.text("CURRENT_DATE"),
        ),
    )

    # 7. Add completed (Boolean) column per ORM
    op.add_column(
        "habit_logs",
        sa.Column("completed", sa.Boolean(), nullable=False, server_default="true"),
    )


def downgrade() -> None:
    # -- Restore habit_logs table (reverse order) --
    # 1. Drop completed column
    op.drop_column("habit_logs", "completed")

    # 2. Drop log_date column
    op.drop_column("habit_logs", "log_date")

    # 3. Restore completed_at column
    op.add_column(
        "habit_logs",
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # -- Restore habits table --
    # 4. Drop user_id index
    op.drop_index(op.f("ix_habits_user_id"), "habits")

    # 5. Restore streak-tracking columns
    op.add_column(
        "habits",
        sa.Column("current_streak", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "habits",
        sa.Column("longest_streak", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "habits", sa.Column("last_completed", sa.DateTime(timezone=True), nullable=True)
    )

    # 6. Drop is_active column
    op.drop_column("habits", "is_active")

    # 7. Alter name column back to String(200)
    op.alter_column(
        "habits",
        "name",
        existing_type=sa.String(length=300),
        type_=sa.String(length=200),
    )
