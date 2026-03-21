"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Dashboard Service Pydantic schemas.
"""

from pydantic import BaseModel


class DailyMetrics(BaseModel):
    """Full daily metrics breakdown."""

    date: str
    habits_completed: int
    total_habits: int
    learning_minutes: int
    calories_consumed: int
    calories_burned: int
    net_calories: int
    productivity_score: int
    notes_created_today: int = 0
    records_created_today: int = 0
    current_streak: int = 0


class OverviewResponse(BaseModel):
    """Simplified overview response for dashboard summary card."""

    date: str
    habits_completed: int
    learning_minutes: int
    calories_balance: int  # net_calories
    productivity_score: int


class WeeklyResponse(BaseModel):
    """Weekly trend data aggregated from daily snapshots."""

    week_start: str
    week_end: str
    days: list[DailyMetrics]
    avg_productivity_score: float
    total_learning_minutes: int
    avg_habits_completed: float
    consistency_score: float
