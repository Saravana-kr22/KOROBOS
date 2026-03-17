"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Canonical Kafka topic subscriptions for KOROBOS background workers.
"""

ANALYTICS_TOPICS = (
    "note.created",
    "note.deleted",
    "note.link.created",
    "habit.created",
    "habit.completed",
    "habit.streak.updated",
    "learning.session.logged",
    "meal.logged",
    "workout.logged",
    "user.registered",
    "user.login",
    "ai.interaction.completed",
    "database.created",
    "record.created",
    "record.updated",
    "record.deleted",
)

NOTIFICATION_TOPICS = ("habit.completed", "habit.reminder.due")

SEARCH_TOPICS = (
    "note.created",
    "note.updated",
    "note.deleted",
    "record.created",
    "record.updated",
    "record.deleted",
)

AI_TOPICS = (
    "note.created",
    "note.updated",
    "learning.session.logged",
    "record.created",
    "record.updated",
    "habit.completed",
    "habit.streak.updated",
)

GRAPH_TOPICS = (
    "note.link.created",
    "note.deleted",
)
