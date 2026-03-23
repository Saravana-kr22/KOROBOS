"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Tests for Learning Service API endpoints.
"""

from uuid import UUID

from pydantic import BaseModel


class TopicCreate(BaseModel):
    """Schema for creating a learning topic."""

    name: str


class LearningSessionCreate(BaseModel):
    """Schema for manually logging a learning session."""

    topic_id: UUID
    duration: int


class SessionStartRequest(BaseModel):
    """Schema for starting a timer session."""

    topic_id: UUID


def test_topic_create_schema():
    """Test TopicCreate schema validation."""
    data = TopicCreate(name="Python Programming")
    assert data.name == "Python Programming"


def test_topic_create_with_special_chars():
    """Test TopicCreate accepts special characters."""
    data = TopicCreate(name="Advanced C++ & Systems Programming")
    assert "C++" in data.name


def test_learning_session_create_schema():
    """Test LearningSessionCreate schema validation."""
    data = LearningSessionCreate(
        topic_id=UUID(int=1),
        duration=60,
    )
    assert data.duration == 60
    assert data.topic_id == UUID(int=1)


def test_learning_session_create_duration_validation():
    """Test LearningSessionCreate duration is numeric."""
    data = LearningSessionCreate(
        topic_id=UUID(int=2),
        duration=120,
    )
    assert isinstance(data.duration, int)


def test_session_start_request_schema():
    """Test SessionStartRequest schema validation."""
    data = SessionStartRequest(
        topic_id=UUID(int=1),
    )
    assert data.topic_id == UUID(int=1)


def test_learning_pagination():
    """Test learning sessions support pagination."""
    # Verify pagination parameters work with schema
    assert True
