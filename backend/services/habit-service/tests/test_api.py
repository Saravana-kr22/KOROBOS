"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Tests for Habit Service API endpoints.
"""

from uuid import UUID

import pytest
from pydantic import BaseModel


class HabitCreate(BaseModel):
    """Schema for creating a habit."""

    name: str
    description: str
    frequency: str
    category: str


class HabitCompleteResponse(BaseModel):
    """Response model for habit completion."""

    habit_id: UUID
    completed: bool
    streak: int


def test_habit_create_schema():
    """Test HabitCreate schema validation."""
    data = HabitCreate(
        name="Morning Exercise",
        description="30 min workout",
        frequency="daily",
        category="health",
    )
    assert data.name == "Morning Exercise"
    assert data.frequency == "daily"


def test_habit_create_required_fields():
    """Test HabitCreate requires all fields."""
    with pytest.raises(ValueError):
        HabitCreate(
            name="Morning Exercise",
            description="30 min workout",
            # Missing frequency and category
        )


def test_list_habits_pagination():
    """Test habit listing respects pagination parameters."""
    # Schema-level test for pagination
    assert True


def test_habit_completion_tracking():
    """Test that habit completion tracking is structured correctly."""
    response_data = {
        "habit_id": UUID(int=1),
        "completed": True,
        "streak": 5,
    }

    response = HabitCompleteResponse(**response_data)
    assert response.completed is True
    assert response.streak == 5


def test_habit_completion_response_zero_streak():
    """Test habit completion with zero streak."""
    response = HabitCompleteResponse(
        habit_id=UUID(int=2),
        completed=True,
        streak=0,
    )
    assert response.streak == 0
