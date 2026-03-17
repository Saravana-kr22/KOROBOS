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

    if event_type == "learning.session.logged":
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

    return None
