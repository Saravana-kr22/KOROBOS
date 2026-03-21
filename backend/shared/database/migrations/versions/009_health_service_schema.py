"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Health Service schema reconciliation and enhancement.

Revision ID: 009_health_service_schema
Revises: 008_learning_service_schema
Create Date: 2026-03-22 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "009_health_service_schema"
down_revision = "008_learning_service_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -- Health Service schema reconciliation and enhancement --
    # The health_logs table was created in 001_initial with value(Float) +
    # metadata(JSONB) but the ORM model uses calories(Int) + duration(Int) +
    # description(Text). Also add Sprint 10 macronutrient and workout type.

    # Drop old columns from 001_initial
    op.drop_column("health_logs", "value")
    op.drop_column("health_logs", "metadata")

    # Add standard columns to match ORM and TimestampMixin
    op.add_column(
        "health_logs",
        sa.Column(
            "calories",
            sa.Integer(),
            nullable=True,
            comment="Calories (for meals or burned during workouts)",
        ),
    )
    op.add_column(
        "health_logs",
        sa.Column(
            "duration",
            sa.Integer(),
            nullable=True,
            comment="Duration in minutes (for workouts)",
        ),
    )
    op.add_column(
        "health_logs",
        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
            comment="Meal description or workout notes",
        ),
    )

    # Add updated_at to match TimestampMixin (created_at exists from 001_initial)
    op.add_column(
        "health_logs",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # Add Sprint 10 macronutrient fields for meal tracking
    op.add_column(
        "health_logs",
        sa.Column("protein", sa.Integer(), nullable=True, comment="Protein in grams"),
    )
    op.add_column(
        "health_logs",
        sa.Column(
            "carbs", sa.Integer(), nullable=True, comment="Carbohydrates in grams"
        ),
    )
    op.add_column(
        "health_logs",
        sa.Column("fat", sa.Integer(), nullable=True, comment="Fat in grams"),
    )

    # Add food_name for meal logging
    op.add_column(
        "health_logs",
        sa.Column(
            "food_name",
            sa.String(length=500),
            nullable=True,
            comment="Name of the meal/food logged",
        ),
    )

    # Add workout_type for workout classification
    op.add_column(
        "health_logs",
        sa.Column(
            "workout_type",
            sa.String(length=100),
            nullable=True,
            comment="Type of workout (running, swimming, etc.)",
        ),
    )

    # Create index on user_id for efficient lookups
    op.create_index(
        op.f("ix_health_logs_user_id"), "health_logs", ["user_id"], unique=False
    )


def downgrade() -> None:
    # Drop new index
    op.drop_index(op.f("ix_health_logs_user_id"), table_name="health_logs")

    # Drop new columns
    op.drop_column("health_logs", "workout_type")
    op.drop_column("health_logs", "food_name")
    op.drop_column("health_logs", "fat")
    op.drop_column("health_logs", "carbs")
    op.drop_column("health_logs", "protein")
    op.drop_column("health_logs", "updated_at")
    op.drop_column("health_logs", "description")
    op.drop_column("health_logs", "duration")
    op.drop_column("health_logs", "calories")

    # Restore original columns from 001_initial
    op.add_column(
        "health_logs",
        sa.Column("metadata", sa.JSON(), nullable=True),
    )
    op.add_column(
        "health_logs",
        sa.Column("value", sa.Float(), nullable=True),
    )
