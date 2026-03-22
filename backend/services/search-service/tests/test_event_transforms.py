"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Unit tests for event transform functions used by the search worker.
"""

from backend.workers.event_transforms import (
    search_document_from_habit_payload,
    search_document_from_health_payload,
    search_document_from_learning_payload,
    search_document_from_payload,
    search_document_from_record_payload,
)

# Test user ID for all tests
USER_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


# -- Note Transform Tests --


def test_note_document_has_required_fields():
    """Note document includes all required fields."""
    payload = {
        "note_id": "note-123",
        "user_id": USER_ID,
        "title": "Test Note",
        "content_md": "# Test Content",
        "tags": ["python", "learning"],
    }

    doc = search_document_from_payload(payload)

    assert doc["id"] == "note-123"
    assert doc["note_id"] == "note-123"
    assert doc["user_id"] == USER_ID
    assert doc["title"] == "Test Note"
    assert doc["content_md"] == "# Test Content"
    assert doc["tags"] == ["python", "learning"]


def test_note_document_id_matches_note_id():
    """Note document 'id' field matches 'note_id'."""
    payload = {
        "note_id": "abc-def-ghi",
        "user_id": USER_ID,
    }

    doc = search_document_from_payload(payload)

    assert doc["id"] == payload["note_id"]
    assert doc["id"] == doc["note_id"]


def test_note_document_defaults_empty_strings():
    """Note document provides empty strings for missing title/content."""
    payload = {
        "note_id": "note-456",
        "user_id": USER_ID,
    }

    doc = search_document_from_payload(payload)

    assert doc["title"] == ""
    assert doc["content_md"] == ""


def test_note_document_defaults_empty_tags():
    """Note document provides empty list for missing tags."""
    payload = {
        "note_id": "note-789",
        "user_id": USER_ID,
        "title": "Note",
    }

    doc = search_document_from_payload(payload)

    assert doc["tags"] == []


# -- Record Transform Tests --


def test_record_document_has_required_fields():
    """Record document includes all required fields."""
    payload = {
        "record_id": "rec-123",
        "database_id": "db-abc",
        "user_id": USER_ID,
        "values": {"name": "Alice", "age": "30"},
    }

    doc = search_document_from_record_payload(payload)

    assert doc["id"] == "rec-123"
    assert doc["record_id"] == "rec-123"
    assert doc["database_id"] == "db-abc"
    assert doc["user_id"] == USER_ID
    assert doc["type"] == "record"


def test_record_document_builds_searchable_content():
    """Record document concatenates values into searchable content."""
    payload = {
        "record_id": "rec-456",
        "database_id": "db-xyz",
        "user_id": USER_ID,
        "values": {"name": "Bob", "role": "Engineer", "team": "Platform"},
    }

    doc = search_document_from_record_payload(payload)

    # All values joined with spaces
    assert "Bob" in doc["content"]
    assert "Engineer" in doc["content"]
    assert "Platform" in doc["content"]


def test_record_document_filters_empty_values():
    """Record document skips empty/None/falsy values."""
    payload = {
        "record_id": "rec-789",
        "database_id": "db-test",
        "user_id": USER_ID,
        "values": {"name": "Charlie", "middle_name": "", "age": None, "city": "NYC"},
    }

    doc = search_document_from_record_payload(payload)

    # Only non-empty values included
    assert "Charlie" in doc["content"]
    assert "NYC" in doc["content"]
    assert "" not in doc["content"].split()  # No empty strings


def test_record_document_empty_values_yields_empty_content():
    """Record document with no values produces empty content string."""
    payload = {
        "record_id": "rec-empty",
        "database_id": "db-empty",
        "user_id": USER_ID,
        "values": {},
    }

    doc = search_document_from_record_payload(payload)

    assert doc["content"] == ""


def test_record_document_missing_optional_fields():
    """Record document provides defaults for missing optional fields."""
    payload = {
        "user_id": USER_ID,
    }

    doc = search_document_from_record_payload(payload)

    assert doc["record_id"] == ""
    assert doc["database_id"] == ""
    assert doc["content"] == ""


# -- Learning Transform Tests (Topic) --


def test_learning_topic_created_has_required_fields():
    """Learning topic document includes all required fields."""
    payload = {
        "topic_id": "123",
        "user_id": USER_ID,
        "name": "Machine Learning",
    }

    doc = search_document_from_learning_payload("learning.topic.created", payload)

    assert doc["id"] == "topic-123"
    assert doc["topic_id"] == "123"
    assert doc["user_id"] == USER_ID
    assert doc["name"] == "Machine Learning"
    assert doc["type"] == "topic"


def test_learning_topic_id_uses_topic_prefix():
    """Learning topic document ID includes 'topic-' prefix."""
    payload = {
        "topic_id": "abc123",
        "user_id": USER_ID,
        "name": "Python",
    }

    doc = search_document_from_learning_payload("learning.topic.created", payload)

    assert doc["id"] == "topic-abc123"


def test_learning_topic_defaults_empty_name():
    """Learning topic document provides empty string for missing name."""
    payload = {
        "topic_id": "topic-456",
        "user_id": USER_ID,
    }

    doc = search_document_from_learning_payload("learning.topic.created", payload)

    assert doc["name"] == ""


# -- Learning Transform Tests (Session) --


def test_learning_session_logged_has_required_fields():
    """Learning session document includes all required fields."""
    payload = {
        "session_id": "123",
        "user_id": USER_ID,
        "topic": "AI Basics",
        "duration": 45,
        "notes": "Covered neural networks",
    }

    doc = search_document_from_learning_payload("learning.session.logged", payload)

    assert doc["id"] == "session-123"
    assert doc["session_id"] == "123"
    assert doc["user_id"] == USER_ID
    assert doc["topic"] == "AI Basics"
    assert doc["duration"] == 45
    assert doc["notes"] == "Covered neural networks"
    assert doc["type"] == "session"


def test_learning_session_completed_creates_session_doc():
    """Learning session.completed creates same document as session.logged."""
    payload = {
        "session_id": "456",
        "user_id": USER_ID,
        "topic": "Data Science",
        "duration": 60,
        "notes": "Analyzed datasets",
    }

    doc = search_document_from_learning_payload("learning.session.completed", payload)

    assert doc["type"] == "session"
    assert doc["session_id"] == "456"
    assert doc["topic"] == "Data Science"


def test_learning_session_id_uses_session_prefix():
    """Learning session document ID includes 'session-' prefix."""
    payload = {
        "session_id": "xyz789",
        "user_id": USER_ID,
        "topic": "Web Dev",
    }

    doc = search_document_from_learning_payload("learning.session.logged", payload)

    assert doc["id"] == "session-xyz789"


def test_learning_session_defaults_duration():
    """Learning session provides 0 for missing duration."""
    payload = {
        "session_id": "session-789",
        "user_id": USER_ID,
        "topic": "Testing",
    }

    doc = search_document_from_learning_payload("learning.session.logged", payload)

    assert doc["duration"] == 0


def test_learning_session_defaults_notes():
    """Learning session provides empty string for missing notes."""
    payload = {
        "session_id": "session-000",
        "user_id": USER_ID,
        "topic": "Refactoring",
    }

    doc = search_document_from_learning_payload("learning.session.logged", payload)

    assert doc["notes"] == ""


# -- Habit Transform Tests --


def test_habit_document_has_required_fields():
    """Habit document includes all required fields."""
    payload = {
        "habit_id": "habit-123",
        "user_id": USER_ID,
        "name": "Morning Run",
        "description": "5k run every morning",
        "frequency": "daily",
    }

    doc = search_document_from_habit_payload(payload)

    assert doc["id"] == "habit-123"
    assert doc["habit_id"] == "habit-123"
    assert doc["user_id"] == USER_ID
    assert doc["name"] == "Morning Run"
    assert doc["description"] == "5k run every morning"
    assert doc["frequency"] == "daily"
    assert doc["type"] == "habit"


def test_habit_id_matches_habit_id():
    """Habit document 'id' field matches 'habit_id'."""
    payload = {
        "habit_id": "h-abc-123",
        "user_id": USER_ID,
    }

    doc = search_document_from_habit_payload(payload)

    assert doc["id"] == payload["habit_id"]
    assert doc["id"] == doc["habit_id"]


def test_habit_defaults_frequency_to_daily():
    """Habit document defaults frequency to 'daily' if missing."""
    payload = {
        "habit_id": "habit-456",
        "user_id": USER_ID,
        "name": "Meditation",
    }

    doc = search_document_from_habit_payload(payload)

    assert doc["frequency"] == "daily"


def test_habit_defaults_empty_strings():
    """Habit document provides empty strings for missing name/description."""
    payload = {
        "habit_id": "habit-789",
        "user_id": USER_ID,
    }

    doc = search_document_from_habit_payload(payload)

    assert doc["name"] == ""
    assert doc["description"] == ""


def test_habit_preserves_frequency():
    """Habit document preserves non-default frequency."""
    payload = {
        "habit_id": "habit-weekly",
        "user_id": USER_ID,
        "name": "Grocery Shopping",
        "frequency": "weekly",
    }

    doc = search_document_from_habit_payload(payload)

    assert doc["frequency"] == "weekly"


# -- Health Transform Tests (Meal) --


def test_meal_document_has_required_fields():
    """Meal document includes all required fields."""
    payload = {
        "log_id": "meal-123",
        "user_id": USER_ID,
        "food_name": "Chicken Salad",
        "description": "Grilled chicken with greens",
        "calories": 450,
        "protein": 35,
        "carbs": 20,
        "fat": 18,
    }

    doc = search_document_from_health_payload("meal.logged", payload)

    assert doc["id"] == "meal-123"
    assert doc["log_id"] == "meal-123"
    assert doc["user_id"] == USER_ID
    assert doc["food_name"] == "Chicken Salad"
    assert doc["description"] == "Grilled chicken with greens"
    assert doc["calories"] == 450
    assert doc["protein"] == 35
    assert doc["carbs"] == 20
    assert doc["fat"] == 18
    assert doc["type"] == "meal"


def test_meal_document_defaults_empty_strings():
    """Meal document provides empty strings for missing food_name/description."""
    payload = {
        "log_id": "meal-456",
        "user_id": USER_ID,
    }

    doc = search_document_from_health_payload("meal.logged", payload)

    assert doc["food_name"] == ""
    assert doc["description"] == ""


def test_meal_document_defaults_zero_calories():
    """Meal document provides 0 for missing calories."""
    payload = {
        "log_id": "meal-789",
        "user_id": USER_ID,
        "food_name": "Apple",
    }

    doc = search_document_from_health_payload("meal.logged", payload)

    assert doc["calories"] == 0


def test_meal_document_includes_optional_macros():
    """Meal document includes optional macro fields (can be None)."""
    payload = {
        "log_id": "meal-000",
        "user_id": USER_ID,
        "food_name": "Mystery Dish",
        "protein": None,
        "carbs": None,
        "fat": None,
    }

    doc = search_document_from_health_payload("meal.logged", payload)

    assert "protein" in doc
    assert "carbs" in doc
    assert "fat" in doc
    assert doc["protein"] is None
    assert doc["carbs"] is None
    assert doc["fat"] is None


# -- Health Transform Tests (Workout) --


def test_workout_document_has_required_fields():
    """Workout document includes all required fields."""
    payload = {
        "log_id": "workout-123",
        "user_id": USER_ID,
        "workout_type": "Running",
        "description": "5K run at pace",
        "duration": 30,
        "calories": 350,
    }

    doc = search_document_from_health_payload("workout.logged", payload)

    assert doc["id"] == "workout-123"
    assert doc["log_id"] == "workout-123"
    assert doc["user_id"] == USER_ID
    assert doc["workout_type"] == "Running"
    assert doc["description"] == "5K run at pace"
    assert doc["duration"] == 30
    assert doc["calories"] == 350
    assert doc["type"] == "workout"


def test_workout_document_defaults_empty_strings():
    """Workout document provides empty strings for missing workout_type/description."""
    payload = {
        "log_id": "workout-456",
        "user_id": USER_ID,
    }

    doc = search_document_from_health_payload("workout.logged", payload)

    assert doc["workout_type"] == ""
    assert doc["description"] == ""


def test_workout_document_defaults_zero_duration():
    """Workout document provides 0 for missing duration."""
    payload = {
        "log_id": "workout-789",
        "user_id": USER_ID,
        "workout_type": "Cycling",
    }

    doc = search_document_from_health_payload("workout.logged", payload)

    assert doc["duration"] == 0


def test_workout_document_defaults_zero_calories():
    """Workout document provides 0 for missing calories."""
    payload = {
        "log_id": "workout-000",
        "user_id": USER_ID,
        "workout_type": "Swimming",
        "duration": 45,
    }

    doc = search_document_from_health_payload("workout.logged", payload)

    assert doc["calories"] == 0


def test_health_missing_log_id_defaults_empty():
    """Health payload with missing log_id defaults to empty string."""
    payload = {
        "user_id": USER_ID,
    }

    doc = search_document_from_health_payload("meal.logged", payload)

    assert doc["id"] == ""
    assert doc["log_id"] == ""


def test_health_missing_user_id_defaults_empty():
    """Health payload with missing user_id defaults to empty string."""
    payload = {
        "log_id": "meal-123",
    }

    doc = search_document_from_health_payload("meal.logged", payload)

    assert doc["user_id"] == ""
