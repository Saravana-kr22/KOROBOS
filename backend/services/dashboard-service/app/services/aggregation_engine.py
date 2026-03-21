"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Aggregation Engine — fetches data from source services.
"""

import httpx
from app.config.settings import DashboardSettings


class AggregationEngine:
    """
    Fetches live data from source services (habits, health, learning).

    Uses httpx.AsyncClient with graceful fallback to empty dict on failures.
    All HTTP calls wrapped in try/except to ensure partial failures don't
    break the entire dashboard response.
    """

    def __init__(self, settings: DashboardSettings):
        self.settings = settings
        self.timeout = 10.0  # seconds

    async def get_habit_data(self, user_id: str, headers: dict) -> dict:
        """
        Fetch today's habit data from habit-service.

        Internal call to `GET {HABIT_SERVICE_URL}/habit-stats`.
        Returns {habits_completed, total_habits, current_streak} or {} on error.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"{self.settings.habit_service_url}/habit-stats"
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()

                return {
                    "habits_completed": data.get("habits_completed", 0),
                    "total_habits": data.get("total_habits", 0),
                    "current_streak": data.get("current_streak", 0),
                }
        except Exception as exc:
            # Log and gracefully degrade
            print(f"Failed to fetch habit data: {exc}")
            return {
                "habits_completed": 0,
                "total_habits": 0,
                "current_streak": 0,
            }

    async def get_health_data(self, user_id: str, headers: dict) -> dict:
        """
        Fetch today's health data from health-service.

        Internal call to `GET {HEALTH_SERVICE_URL}/health/daily`.
        Returns {calories_consumed, calories_burned, net_calories} or {} on error.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"{self.settings.health_service_url}/health/daily"
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()

                return {
                    "calories_consumed": data.get("calories_consumed", 0),
                    "calories_burned": data.get("calories_burned", 0),
                    "net_calories": data.get("net_calories", 0),
                }
        except Exception as exc:
            # Log and gracefully degrade
            print(f"Failed to fetch health data: {exc}")
            return {
                "calories_consumed": 0,
                "calories_burned": 0,
                "net_calories": 0,
            }

    async def get_learning_data(self, user_id: str, headers: dict) -> dict:
        """
        Fetch today's learning data from learning-service.

        Internal call to `GET {LEARNING_SERVICE_URL}/learning/sessions?date=today`.
        Sums up duration_minutes from all sessions today.
        Returns {learning_minutes: int} or {} on error.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"{self.settings.learning_service_url}/learning/sessions"
                params = {"date": "today"}
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                data = response.json()

                # Sum duration_minutes from all sessions in the response
                sessions = data.get("sessions", [])
                learning_minutes = sum(s.get("duration_minutes", 0) for s in sessions)

                return {"learning_minutes": max(0, int(learning_minutes))}
        except Exception as exc:
            # Log and gracefully degrade
            print(f"Failed to fetch learning data: {exc}")
            return {"learning_minutes": 0}

    async def get_notes_data(self, user_id: str, headers: dict) -> dict:
        """
        Fetch notes activity data from notes-service.

        Internal call to `GET {NOTES_SERVICE_URL}/stats`.
        Returns {notes_created_today, total_notes} or {} on error.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"{self.settings.notes_service_url}/stats"
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()

                return {
                    "notes_created_today": data.get("notes_created_today", 0),
                    "total_notes": data.get("total_notes", 0),
                }
        except Exception as exc:
            # Log and gracefully degrade
            print(f"Failed to fetch notes data: {exc}")
            return {"notes_created_today": 0, "total_notes": 0}

    async def get_database_data(self, user_id: str, headers: dict) -> dict:
        """
        Fetch database activity data from database-service.

        Internal call to `GET {DATABASE_SERVICE_URL}/stats`.
        Returns {total_databases, records_created_today} or {} on error.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"{self.settings.database_service_url}/stats"
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()

                return {
                    "total_databases": data.get("total_databases", 0),
                    "records_created_today": data.get("records_created_today", 0),
                }
        except Exception as exc:
            # Log and gracefully degrade
            print(f"Failed to fetch database data: {exc}")
            return {"total_databases": 0, "records_created_today": 0}
