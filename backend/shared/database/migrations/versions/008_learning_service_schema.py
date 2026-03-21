"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Migration 008 — Learning Service schema overhaul.

Changes:
- Fix learning_sessions: rename duration_minutes → duration
- Drop unused focus_score column
- Add missing columns: notes, updated_at, status, start_time, end_time, topic_id
- Add user_id index on learning_sessions
- Create topics table (Topic entity)
- Create session_notes join table (links sessions to notes)
- Add FK from learning_sessions.topic_id → topics.id

Revision ID: 008_learning_service_schema
Revises: 007_push_tokens
Create Date: 2026-03-19 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "008_learning_service_schema"
down_revision = "007_push_tokens"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- Fix learning_sessions ---

    # 1. Rename duration_minutes → duration
    op.alter_column(
        "learning_sessions",
        "duration_minutes",
        new_column_name="duration",
        existing_type=sa.Integer(),
        existing_nullable=False,
    )

    # 2. Drop unused focus_score
    op.drop_column("learning_sessions", "focus_score")

    # 3. Add missing columns
    op.add_column(
        "learning_sessions",
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.add_column(
        "learning_sessions",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.add_column(
        "learning_sessions",
        sa.Column(
            "status",
            sa.String(20),
            server_default="completed",
            nullable=False,
        ),
    )
    op.add_column(
        "learning_sessions",
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "learning_sessions",
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "learning_sessions",
        sa.Column(
            "topic_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )

    # 4. Add user_id index (missing from 001_initial)
    op.create_index(
        "ix_learning_sessions_user_id",
        "learning_sessions",
        ["user_id"],
    )

    # --- Create topics table ---
    op.create_table(
        "topics",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(300), nullable=False),
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
    op.create_index("ix_topics_user_id", "topics", ["user_id"])

    # --- Create session_notes join table ---
    op.create_table(
        "session_notes",
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "note_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["learning_sessions.id"],
            ondelete="CASCADE",
            name="fk_session_notes_session_id",
        ),
        sa.PrimaryKeyConstraint("session_id", "note_id"),
    )

    # --- Add FK from learning_sessions.topic_id → topics.id ---
    op.create_foreign_key(
        "fk_learning_sessions_topic_id",
        "learning_sessions",
        "topics",
        ["topic_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_learning_sessions_topic_id", "learning_sessions", type_="foreignkey"
    )
    op.drop_table("session_notes")
    op.drop_index("ix_topics_user_id", table_name="topics")
    op.drop_table("topics")
    op.drop_index("ix_learning_sessions_user_id", table_name="learning_sessions")
    op.drop_column("learning_sessions", "topic_id")
    op.drop_column("learning_sessions", "end_time")
    op.drop_column("learning_sessions", "start_time")
    op.drop_column("learning_sessions", "status")
    op.drop_column("learning_sessions", "updated_at")
    op.drop_column("learning_sessions", "notes")
    op.add_column(
        "learning_sessions",
        sa.Column("focus_score", sa.Integer(), nullable=True),
    )
    op.alter_column(
        "learning_sessions",
        "duration",
        new_column_name="duration_minutes",
        existing_type=sa.Integer(),
        existing_nullable=False,
    )
