"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Feature Engineering Service — computes normalized feature scores from analytics data.
"""

from uuid import UUID

import httpx
from pydantic import BaseModel, Field

from backend.shared.logging.logger import get_logger

logger = get_logger("feature-engineering")


class FeatureVector(BaseModel):
    """Normalized feature vector (0-100 scale)."""

    habit_consistency_score: float = Field(
        ..., ge=0.0, le=100.0, description="Habit consistency 0-100"
    )
    learning_velocity: float = Field(
        ..., ge=0.0, le=100.0, description="Learning velocity 0-100"
    )
    health_balance_index: float = Field(
        ..., ge=0.0, le=100.0, description="Health balance 0-100"
    )
    productivity_score: float = Field(
        ..., ge=0.0, le=100.0, description="Overall productivity 0-100"
    )
    graph_connectivity_score: float = Field(
        ..., ge=0.0, le=100.0, description="Knowledge graph connectivity 0-100"
    )


class FeatureEngineeringService:
    """Computes normalized feature scores from analytics-service."""

    def __init__(self, analytics_service_url: str, graph_service_url: str):
        self.analytics_url = analytics_service_url.rstrip("/")
        self.graph_url = graph_service_url.rstrip("/")

    async def get_feature_vector(
        self, user_id: UUID, user_id_header: str = "X-User-ID"
    ) -> FeatureVector:
        """
        Fetch analytics data and compute normalized feature vector.

        Returns 50.0 for any metric that fails to fetch (graceful degradation).
        """
        async with httpx.AsyncClient(timeout=10.0) as client:
            habit_score = await self._get_habit_consistency(
                client, user_id, user_id_header
            )
            learning_score = await self._get_learning_velocity(
                client, user_id, user_id_header
            )
            health_score = await self._get_health_balance(
                client, user_id, user_id_header
            )
            productivity_score = await self._get_productivity_score(
                client, user_id, user_id_header
            )
            graph_score = await self._get_graph_connectivity(
                client, user_id, user_id_header
            )

        return FeatureVector(
            habit_consistency_score=habit_score,
            learning_velocity=learning_score,
            health_balance_index=health_score,
            productivity_score=productivity_score,
            graph_connectivity_score=graph_score,
        )

    async def _get_habit_consistency(
        self, client: httpx.AsyncClient, user_id: UUID, header: str
    ) -> float:
        """Habit consistency from analytics/habits endpoint."""
        try:
            response = await client.get(
                f"{self.analytics_url}/habits",
                headers={header: str(user_id)},
                params={"limit": 1},
            )
            if response.status_code == 200:
                data = response.json()
                if "data" in data and data["data"]:
                    # Analytics returns raw metric; assume it's already 0-100
                    # If not present, default to 50.0
                    return float(data.get("completion_rate", 50.0))
                # If no habits data, return default
                return 50.0
            return 50.0
        except Exception as e:
            logger.warning(f"Failed to fetch habit consistency: {e}")
            return 50.0

    async def _get_learning_velocity(
        self, client: httpx.AsyncClient, user_id: UUID, header: str
    ) -> float:
        """Learning velocity (learning hours * 10, capped at 100)."""
        try:
            response = await client.get(
                f"{self.analytics_url}/learning",
                headers={header: str(user_id)},
                params={"limit": 1},
            )
            if response.status_code == 200:
                data = response.json()
                if "data" in data and data["data"]:
                    # Assume learning returns hours
                    hours = float(data.get("learning_hours", 0.0))
                    # Normalize: target is ~10 hours/week, so 1-2 hours/day is good
                    # Scale: 10 hours = 100%, cap at 100
                    velocity = min(hours * 10, 100.0)
                    return max(velocity, 0.0)
                return 50.0
            return 50.0
        except Exception as e:
            logger.warning(f"Failed to fetch learning velocity: {e}")
            return 50.0

    async def _get_health_balance(
        self, client: httpx.AsyncClient, user_id: UUID, header: str
    ) -> float:
        """Health balance index (100 - min(|surplus|/10, 100))."""
        try:
            response = await client.get(
                f"{self.analytics_url}/health",
                headers={header: str(user_id)},
                params={"limit": 1},
            )
            if response.status_code == 200:
                data = response.json()
                if "data" in data and data["data"]:
                    # Try to extract calorie surplus from data
                    # Expected structure: consumed, burned, net
                    net = float(data.get("net_calories", 0.0))
                    # Normalize: |500 kcal surplus| = 50 score (moderate issue)
                    # |2000 kcal surplus| = 0 score (severe issue)
                    abs_surplus = abs(net)
                    penalty = min(abs_surplus / 10.0, 100.0)
                    balance = 100.0 - penalty
                    return max(balance, 0.0)
                return 50.0
            return 50.0
        except Exception as e:
            logger.warning(f"Failed to fetch health balance: {e}")
            return 50.0

    async def _get_productivity_score(
        self, client: httpx.AsyncClient, user_id: UUID, header: str
    ) -> float:
        """Overall productivity score from analytics overview."""
        try:
            response = await client.get(
                f"{self.analytics_url}/overview",
                headers={header: str(user_id)},
            )
            if response.status_code == 200:
                data = response.json()
                if "data" in data:
                    # Assume overview includes productivity_score (already 0-100)
                    return float(data.get("productivity_score", 50.0))
                return 50.0
            return 50.0
        except Exception as e:
            logger.warning(f"Failed to fetch productivity score: {e}")
            return 50.0

    async def _get_graph_connectivity(
        self, client: httpx.AsyncClient, user_id: UUID, header: str
    ) -> float:
        """Knowledge graph connectivity score."""
        try:
            response = await client.get(
                f"{self.graph_url}/stats/{user_id}",
                headers={header: str(user_id)},
            )
            if response.status_code == 200:
                data = response.json()
                if "data" in data:
                    # Assume graph service returns connectivity_score (0-100)
                    return float(data.get("connectivity_score", 50.0))
                return 50.0
            # If graph service not available or no data, default
            return 50.0
        except Exception as e:
            logger.warning(f"Failed to fetch graph connectivity: {e}")
            return 50.0
