"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Aggregation Engine — fetches processed analytics from analytics-service.
"""

import httpx
from app.config.settings import DashboardSettings


class AggregationEngine:
    """
    Fetches processed analytics from analytics-service.

    Uses httpx.AsyncClient with graceful fallback to empty dict on failures.
    All HTTP calls wrapped in try/except to ensure partial failures don't
    break the entire dashboard response.
    """

    def __init__(self, settings: DashboardSettings):
        self.settings = settings
        self.timeout = 10.0  # seconds

    async def get_analytics_overview(self, user_id: str, headers: dict) -> dict:
        """
        Fetch cross-domain analytics overview from analytics-service.

        Internal call to `GET /analytics/overview` endpoint.
        Returns {productivity_score, habits, learning, health, knowledge}
        or {} on error.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"{self.settings.analytics_service_url}/analytics/overview"
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()

                # Extract analytics data from response
                overview_data = data.get("data", {})
                return {
                    "productivity_score": overview_data.get("productivity_score", 0),
                    "habits": overview_data.get("habits", {}),
                    "learning": overview_data.get("learning", {}),
                    "health": overview_data.get("health", {}),
                    "knowledge": overview_data.get("knowledge", {}),
                }
        except Exception as exc:
            # Log and gracefully degrade
            print(f"Failed to fetch analytics overview: {exc}")
            return {
                "productivity_score": 0,
                "habits": {},
                "learning": {},
                "health": {},
                "knowledge": {},
            }

    async def get_habit_data(self, user_id: str, headers: dict) -> dict:
        """
        Fetch habit metrics from analytics-service.

        Internal call to `GET {ANALYTICS_SERVICE_URL}/analytics/overview`.
        Returns {completion_rate, current_streak} from habits domain.
        """
        try:
            overview = await self.get_analytics_overview(user_id, headers)
            habits = overview.get("habits", {})
            return {
                "habits_completed": habits.get("completion_rate", 0),
                "current_streak": habits.get("current_streak", 0),
                "total_habits": 0,  # Not tracked in analytics service
            }
        except Exception as exc:
            print(f"Failed to fetch habit data: {exc}")
            return {
                "habits_completed": 0,
                "total_habits": 0,
                "current_streak": 0,
            }

    async def get_health_data(self, user_id: str, headers: dict) -> dict:
        """
        Fetch health metrics from analytics-service.

        Internal call to `GET {ANALYTICS_SERVICE_URL}/analytics/health`.
        Returns {intake, burned, balance} or {} on error.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"{self.settings.analytics_service_url}/analytics/health"
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()

                health_data = data.get("data", {}).get("current", {})
                return {
                    "calories_consumed": health_data.get("intake", 0),
                    "calories_burned": health_data.get("burned", 0),
                    "net_calories": health_data.get("balance", 0),
                }
        except Exception as exc:
            print(f"Failed to fetch health data: {exc}")
            return {
                "calories_consumed": 0,
                "calories_burned": 0,
                "net_calories": 0,
            }

    async def get_learning_data(self, user_id: str, headers: dict) -> dict:
        """
        Fetch learning metrics from analytics-service.

        Internal call to `GET {ANALYTICS_SERVICE_URL}/analytics/overview`.
        Returns {learning_minutes} from learning domain.
        """
        try:
            overview = await self.get_analytics_overview(user_id, headers)
            learning = overview.get("learning", {})
            learning_hours = learning.get("learning_hours", 0)
            # Convert hours to minutes
            learning_minutes = int(learning_hours * 60)
            return {"learning_minutes": learning_minutes}
        except Exception as exc:
            print(f"Failed to fetch learning data: {exc}")
            return {"learning_minutes": 0}

    async def get_notes_data(self, user_id: str, headers: dict) -> dict:
        """
        Fetch notes activity from analytics-service.

        Internal call to `GET {ANALYTICS_SERVICE_URL}/analytics/overview`.
        Returns {notes_created_today} from knowledge domain.
        """
        try:
            overview = await self.get_analytics_overview(user_id, headers)
            knowledge = overview.get("knowledge", {})
            return {
                "notes_created_today": knowledge.get("notes_created", 0),
                "total_notes": 0,  # Not tracked in overview
            }
        except Exception as exc:
            print(f"Failed to fetch notes data: {exc}")
            return {"notes_created_today": 0, "total_notes": 0}

    async def get_database_data(self, user_id: str, headers: dict) -> dict:
        """
        Fetch database activity from analytics-service.

        Internal call to `GET {ANALYTICS_SERVICE_URL}/analytics/overview`.
        Returns {records_created_today} from knowledge domain.
        """
        try:
            overview = await self.get_analytics_overview(user_id, headers)
            knowledge = overview.get("knowledge", {})
            return {
                "total_databases": 0,  # Not tracked in overview
                "records_created_today": knowledge.get("records_created", 0),
            }
        except Exception as exc:
            print(f"Failed to fetch database data: {exc}")
            return {"total_databases": 0, "records_created_today": 0}
