"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Migration 003 — Fix notes schema to align with ORM models.

Changes:
  - notes: rename 'content' → 'content_md', drop 'is_encrypted'
  - tags: change 'id' from INTEGER to UUID
  - note_tags: replace composite PK with UUID 'id', update tag_id FK type to UUID
  - note_links: rename 'source_id' → 'source_note_id', 'target_id' → 'target_note_id'

Revision ID: 003_notes_schema_fix
Revises: 002_auth_enhancement
Create Date: 2026-03-15 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "003_notes_schema_fix"
down_revision = "002_auth_enhancement"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -- notes table --
    op.alter_column("notes", "content", new_column_name="content_md")
    op.drop_column("notes", "is_encrypted")

    # -- note_links: rename FK columns --
    # Drop existing FKs before renaming
    op.drop_constraint("note_links_source_id_fkey", "note_links", type_="foreignkey")
    op.drop_constraint("note_links_target_id_fkey", "note_links", type_="foreignkey")
    op.alter_column("note_links", "source_id", new_column_name="source_note_id")
    op.alter_column("note_links", "target_id", new_column_name="target_note_id")
    op.create_foreign_key(
        "note_links_source_note_id_fkey",
        "note_links",
        "notes",
        ["source_note_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "note_links_target_note_id_fkey",
        "note_links",
        "notes",
        ["target_note_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # -- tags: change id from INTEGER to UUID --
    # note_tags references tags.id so we must drop it first, rebuild, then recreate
    op.drop_table("note_tags")

    # Add a temporary UUID column, populate, then swap
    op.add_column(
        "tags", sa.Column("uuid_id", postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.execute("UPDATE tags SET uuid_id = gen_random_uuid()")
    op.drop_constraint("tags_pkey", "tags", type_="primary")
    op.drop_column("tags", "id")
    op.alter_column("tags", "uuid_id", new_column_name="id", nullable=False)
    op.create_primary_key("tags_pkey", "tags", ["id"])

    # Recreate note_tags with UUID tag_id and its own UUID PK
    op.create_table(
        "note_tags",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("note_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tag_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["note_id"], ["notes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    # -- note_tags: revert to composite PK with integer tag_id --
    op.drop_table("note_tags")

    # Revert tags id to integer (data loss — tags will be re-seeded)
    op.drop_constraint("tags_pkey", "tags", type_="primary")
    op.drop_column("tags", "id")
    op.add_column(
        "tags",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
    )
    op.create_primary_key("tags_pkey", "tags", ["id"])

    op.create_table(
        "note_tags",
        sa.Column("note_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["note_id"], ["notes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("note_id", "tag_id"),
    )

    # -- note_links: revert column names --
    op.drop_constraint(
        "note_links_source_note_id_fkey", "note_links", type_="foreignkey"
    )
    op.drop_constraint(
        "note_links_target_note_id_fkey", "note_links", type_="foreignkey"
    )
    op.alter_column("note_links", "source_note_id", new_column_name="source_id")
    op.alter_column("note_links", "target_note_id", new_column_name="target_id")
    op.create_foreign_key(
        "note_links_source_id_fkey",
        "note_links",
        "notes",
        ["source_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "note_links_target_id_fkey",
        "note_links",
        "notes",
        ["target_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # -- notes: revert column name and restore is_encrypted --
    op.alter_column("notes", "content_md", new_column_name="content")
    op.add_column(
        "notes",
        sa.Column(
            "is_encrypted",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
