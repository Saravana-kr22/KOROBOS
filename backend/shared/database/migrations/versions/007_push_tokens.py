"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Migration 007 — Create Push Tokens table.

Adds the `push_tokens` table for mobile push notification support:
- Store user push tokens from Expo/FCM/APNs
- Track platform (iOS/Android)
- Enable batch push notification delivery

Revision ID: 007_push_tokens
Revises: 006_habit_schedules
Create Date: 2026-03-16 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "007_push_tokens"
down_revision = "006_habit_schedules"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -- Push Tokens table --
    op.create_table(
        "push_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token", sa.Text(), nullable=False),
        sa.Column("platform", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token", name="uq_push_tokens_token"),
    )
    op.create_index(op.f("ix_push_tokens_user_id"), "push_tokens", ["user_id"])


def downgrade() -> None:
    # -- Restore --
    op.drop_index(op.f("ix_push_tokens_user_id"), "push_tokens")
    op.drop_constraint("uq_push_tokens_token", "push_tokens", type_="unique")
    op.drop_table("push_tokens")
