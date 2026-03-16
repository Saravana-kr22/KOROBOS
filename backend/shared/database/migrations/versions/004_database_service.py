"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Migration 004 — Create Structured Database System tables.

Introduces a Notion-style database system with:
  - databases: user-owned custom database definitions
  - properties: dynamic fields with type constraints and options (JSONB)
  - records: data rows within each database (EAV pattern)
  - record_values: Entity-Attribute-Value storage for record fields

Design decisions:
  - JSONB 'options' avoids separate property_options table for type-specific config
  - Composite PK on record_values enforces one value per (record, property) pair
  - Soft 'note_id' reference without FK — loose coupling across microservices
  - Index on (property_id, value) optimizes filtered queries in EAV pattern

Revision ID: 004_database_service
Revises: 003_notes_schema_fix
Create Date: 2026-03-15 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "004_database_service"
down_revision = "003_notes_schema_fix"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -- Database Service: databases --
    op.create_table(
        "databases",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=500), nullable=False),
        sa.Column("icon", sa.String(length=100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
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
    op.create_index(
        op.f("ix_databases_user_id"), "databases", ["user_id"], unique=False
    )

    # -- Database Service: properties --
    op.create_table(
        "properties",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("database_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("options", postgresql.JSONB(), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["database_id"], ["databases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_properties_database_id"),
        "properties",
        ["database_id"],
        unique=False,
    )

    # Add CHECK constraint for property type
    op.execute(
        """
        ALTER TABLE properties
        ADD CONSTRAINT ck_properties_type
        CHECK (type IN ('text', 'number', 'boolean', 'date', 'select',
               'multi_select', 'relation'))
        """
    )

    # -- Database Service: records --
    op.create_table(
        "records",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("database_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("note_id", postgresql.UUID(as_uuid=True), nullable=True),
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
        sa.ForeignKeyConstraint(["database_id"], ["databases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_records_database_id"), "records", ["database_id"], unique=False
    )
    op.create_index(op.f("ix_records_note_id"), "records", ["note_id"], unique=False)

    # -- Database Service: record_values (EAV) --
    op.create_table(
        "record_values",
        sa.Column("record_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("property_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("value", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["record_id"], ["records.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["property_id"], ["properties.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("record_id", "property_id"),
    )
    op.create_index(
        op.f("ix_record_values_property_value"),
        "record_values",
        ["property_id", "value"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_record_values_property_value"), table_name="record_values")
    op.drop_table("record_values")
    op.drop_index(op.f("ix_records_note_id"), table_name="records")
    op.drop_index(op.f("ix_records_database_id"), table_name="records")
    op.drop_table("records")
    op.drop_index(op.f("ix_properties_database_id"), table_name="properties")
    op.drop_table("properties")
    op.drop_index(op.f("ix_databases_user_id"), table_name="databases")
    op.drop_table("databases")
