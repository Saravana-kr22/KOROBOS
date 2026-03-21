"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Pure event-to-action transforms used by worker handlers.
"""

from typing import Any


def analytics_metric_for_event(
    event_type: str, payload: dict[str, Any]
) -> tuple[str, float] | None:
    if event_type == "note.created":
        return "notes.created", 1.0
    if event_type == "note.deleted":
        return "notes.deleted", 1.0
    if event_type == "note.link.created":
        return "notes.links.created", 1.0
    if event_type == "habit.created":
        return "habits.created", 1.0
    if event_type == "habit.completed":
        return "habits.completed", float(payload.get("streak", 1))
    if event_type == "habit.streak.updated":
        return "habits.streak", float(payload.get("streak", 0))
    if event_type == "learning.session.logged":
        return "learning.minutes", float(payload.get("duration", 0))
    if event_type == "learning.session.completed":
        return "learning.minutes", float(payload.get("duration", 0))
    if event_type == "learning.session.started":
        return "learning.sessions.started", 1.0
    if event_type == "learning.topic.created":
        return "learning.topics.created", 1.0
    if event_type == "meal.logged":
        return "calories.intake", float(payload.get("calories", 0))
    if event_type == "workout.logged":
        return "workout.minutes", float(payload.get("duration", 0))
    if event_type == "user.registered":
        return "users.registered", 1.0
    if event_type == "user.login":
        return "auth.logins", 1.0
    if event_type == "ai.interaction.completed":
        return "ai.interactions.completed", 1.0
    if event_type == "database.created":
        return "databases.created", 1.0
    if event_type == "record.created":
        return "records.created", 1.0
    if event_type == "record.updated":
        return "records.updated", 1.0
    if event_type == "record.deleted":
        return "records.deleted", 1.0
    return None


def notification_content_for_event(
    event_type: str, payload: dict[str, Any]
) -> tuple[str, str] | None:
    if event_type == "habit.completed":
        streak = payload.get("streak")
        title = "Habit completed 🎯"
        if streak:
            body = f"Great job! Your current streak is {streak} days."
        else:
            body = "Great job completing your habit today!"
        return title, body
    if event_type == "habit.reminder.due":
        habit_name = payload.get("habit_name", "Your habit")
        title = "Habit Reminder ⏰"
        body = f"Time to complete '{habit_name}'!"
        return title, body
    return None


def search_document_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": payload["note_id"],
        "note_id": payload["note_id"],
        "user_id": payload["user_id"],
        "title": payload.get("title", ""),
        "content_md": payload.get("content_md", ""),
        "tags": payload.get("tags", []),
    }


def search_document_from_record_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Transform a database record event into a Meilisearch document."""
    record_id = payload.get("record_id", "")
    database_id = payload.get("database_id", "")

    # Build searchable content from record values
    values = payload.get("values", {})
    content_parts = [str(v) for v in values.values() if v]
    searchable_content = " ".join(content_parts)

    return {
        "id": record_id,
        "record_id": record_id,
        "database_id": database_id,
        "user_id": payload.get("user_id", ""),
        "content": searchable_content,
        "type": "record",
    }


def search_document_from_learning_payload(
    event_type: str, payload: dict[str, Any]
) -> dict[str, Any]:
    """Transform a learning event to a Meilisearch document."""
    if event_type == "learning.topic.created":
        return {
            "id": f"topic-{payload['topic_id']}",
            "topic_id": payload["topic_id"],
            "user_id": payload["user_id"],
            "name": payload.get("name", ""),
            "type": "topic",
        }
    # learning.session.logged and learning.session.completed
    return {
        "id": f"session-{payload['session_id']}",
        "session_id": payload["session_id"],
        "user_id": payload["user_id"],
        "topic": payload.get("topic", ""),
        "duration": payload.get("duration", 0),
        "notes": payload.get("notes", ""),
        "type": "session",
    }


def ai_prompt_for_event(
    event_type: str, payload: dict[str, Any]
) -> dict[str, Any] | None:
    if event_type == "note.created":
        title = payload.get("title", "Untitled note")
        content_md = payload.get("content_md", "")
        return {
            "interaction_type": "summary",
            "prompt": (
                "Create a concise summary and action items for the note "
                f"'{title}'.\n\n{content_md}"
            ),
            "metadata_json": {
                "source_event": event_type,
                "note_id": payload.get("note_id"),
            },
        }

    if event_type == "note.updated":
        title = payload.get("title", payload.get("note_id", "updated note"))
        content_md = payload.get("content_md", "")
        return {
            "interaction_type": "summary",
            "prompt": (
                "Refresh the summary and key takeaways for the note "
                f"'{title}'.\n\n{content_md}"
            ),
            "metadata_json": {
                "source_event": event_type,
                "note_id": payload.get("note_id"),
            },
        }

    if event_type in ("learning.session.logged", "learning.session.completed"):
        topic = payload.get("topic", "learning session")
        duration = payload.get("duration", 0)
        notes = payload.get("notes", "")
        return {
            "interaction_type": "recommendation",
            "prompt": (
                f"Suggest the next best learning steps for '{topic}' after "
                f"{duration} minutes of study.\n\n{notes}"
            ),
            "metadata_json": {
                "source_event": event_type,
                "session_id": payload.get("session_id"),
            },
        }

    if event_type == "learning.topic.created":
        topic_name = payload.get("name", "new topic")
        return {
            "interaction_type": "gap_analysis",
            "prompt": (
                f"A user just created a new learning topic: '{topic_name}'. "
                "Identify key knowledge areas and prerequisites needed. "
                "What are the essential concepts to focus on?"
            ),
            "metadata_json": {
                "source_event": event_type,
                "topic_id": payload.get("topic_id"),
            },
        }

    if event_type == "record.created":
        database_id = payload.get("database_id", "")
        values = payload.get("values", {})
        values_str = "\n".join(f"{k}: {v}" for k, v in values.items() if v)
        return {
            "interaction_type": "insight",
            "prompt": (
                "Generate insights about this new database record in "
                f"'{database_id}':\n\n{values_str}"
            ),
            "metadata_json": {
                "source_event": event_type,
                "record_id": payload.get("record_id"),
                "database_id": database_id,
            },
        }

    if event_type == "record.updated":
        database_id = payload.get("database_id", "")
        values = payload.get("values", {})
        values_str = "\n".join(f"{k}: {v}" for k, v in values.items() if v)
        return {
            "interaction_type": "insight",
            "prompt": (
                f"Update insights for modified database record in '{database_id}':\n\n"
                f"{values_str}"
            ),
            "metadata_json": {
                "source_event": event_type,
                "record_id": payload.get("record_id"),
                "database_id": database_id,
            },
        }

    if event_type == "habit.completed":
        habit_id = payload.get("habit_id", "")
        streak = payload.get("streak", 0)
        return {
            "interaction_type": "recommendation",
            "prompt": (
                f"A user just completed a habit (ID: {habit_id}) "
                f"and has a {streak}-day streak. "
                "Suggest 2-3 strategies to maintain habit momentum."
            ),
            "metadata_json": {
                "source_event": event_type,
                "habit_id": habit_id,
                "streak": streak,
            },
        }

    if event_type == "habit.streak.updated":
        streak = payload.get("streak", 0)
        habit_id = payload.get("habit_id", "")
        return {
            "interaction_type": "insight",
            "prompt": (
                f"A habit (ID: {habit_id}) streak has been updated to {streak} days. "
                "Provide a brief motivational insight about this progress."
            ),
            "metadata_json": {
                "source_event": event_type,
                "habit_id": habit_id,
                "streak": streak,
            },
        }

    if event_type == "meal.logged":
        food_name = payload.get("food_name", "meal")
        calories = payload.get("calories", 0)
        protein = payload.get("protein", "unknown")
        carbs = payload.get("carbs", "unknown")
        fat = payload.get("fat", "unknown")
        return {
            "interaction_type": "recommendation",
            "prompt": (
                f"A user just logged a meal: {food_name} ({calories} kcal). "
                f"Macros: protein={protein}g, carbs={carbs}g, fat={fat}g. "
                "Provide 2-3 balanced nutrition recommendations for their next "
                "meal based on this intake."
            ),
            "metadata_json": {
                "source_event": event_type,
                "food_name": food_name,
                "calories": calories,
            },
        }

    if event_type == "workout.logged":
        workout_type = payload.get("workout_type", "workout")
        duration = payload.get("duration", 0)
        calories_burned = payload.get("calories", 0)
        return {
            "interaction_type": "recommendation",
            "prompt": (
                f"A user just completed a {workout_type} workout for "
                f"{duration} minutes (~{calories_burned} kcal burned). "
                "Suggest 2-3 ways to improve their workout routine or "
                "cross-training opportunities."
            ),
            "metadata_json": {
                "source_event": event_type,
                "workout_type": workout_type,
                "duration": duration,
                "calories_burned": calories_burned,
            },
        }

    if event_type == "dashboard.updated":
        productivity_score = payload.get("productivity_score", 0)
        habits_completed = payload.get("habits_completed", 0)
        learning_minutes = payload.get("learning_minutes", 0)
        calories_balance = payload.get("calories_balance", 0)
        return {
            "interaction_type": "insight",
            "prompt": (
                f"User achieved productivity score {productivity_score}/100 today. "
                f"Habits: {habits_completed} completed, "
                f"Learning: {learning_minutes}min, "
                f"Calories balance: {calories_balance}kcal. "
                "Suggest 1 actionable improvement for tomorrow's routine."
            ),
            "metadata_json": {
                "source_event": event_type,
                "productivity_score": productivity_score,
                "habits_completed": habits_completed,
                "learning_minutes": learning_minutes,
                "calories_balance": calories_balance,
            },
        }

    return None
