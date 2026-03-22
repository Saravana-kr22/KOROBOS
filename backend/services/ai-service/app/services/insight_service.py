"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Insight Service — generates rule-based insights from feature vectors.
"""

import json
from typing import Optional
from uuid import UUID

import redis.asyncio as aioredis
from app.repositories.insight_repository import InsightRepository
from app.services.feature_engineering import FeatureVector
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.logging.logger import get_logger

logger = get_logger("insight-service")

# Insight generation rules (threshold-based)
INSIGHT_RULES = [
    {
        "feature": "habit_consistency_score",
        "insight_type": "behavioral",
        "high_threshold": 70,
        "high_text": "You are most consistent on weekdays — keep this momentum!",
        "low_threshold": 40,
        "low_text": (
            "Your habit consistency needs improvement. "
            "Try breaking habits into smaller steps."
        ),
        "confidence_high": 0.95,
        "confidence_low": 0.85,
    },
    {
        "feature": "learning_velocity",
        "insight_type": "performance",
        "high_threshold": 50,
        "high_text": "Your learning time is on target. Great knowledge pace!",
        "low_threshold": 30,
        "low_text": (
            "Your learning time is below target. "
            "Allocate more time for skill development."
        ),
        "confidence_high": 0.90,
        "confidence_low": 0.80,
    },
    {
        "feature": "health_balance_index",
        "insight_type": "health",
        "high_threshold": 80,
        "high_text": "Your calorie balance is excellent!",
        "low_threshold": 50,
        "low_text": (
            "You are in calorie surplus. " "Consider adjusting meals or exercise."
        ),
        "confidence_high": 0.88,
        "confidence_low": 0.78,
    },
    {
        "feature": "graph_connectivity_score",
        "insight_type": "knowledge",
        "high_threshold": 70,
        "high_text": "You frequently link notes. Your knowledge network grows!",
        "low_threshold": 30,
        "low_text": (
            "Your knowledge connections are sparse. "
            "Link related notes to build your graph."
        ),
        "confidence_high": 0.85,
        "confidence_low": 0.75,
    },
]

# Cache settings
CACHE_TTL_SECONDS = 300  # 5 minutes


class InsightService:
    """Service for generating and managing insights."""

    def __init__(
        self,
        session: AsyncSession,
        redis: Optional[aioredis.Redis],
        settings,
    ):
        self.repo = InsightRepository(session)
        self.redis = redis
        self.settings = settings

    async def generate_insights(
        self, user_id: UUID, feature_vector: FeatureVector
    ) -> list:
        """
        Generate rule-based insights from feature vector.

        Returns list of AIInsight objects.
        """
        insights = []

        for rule in INSIGHT_RULES:
            feature_value = getattr(feature_vector, rule["feature"])

            # High score insights
            if feature_value >= rule["high_threshold"]:
                insight = await self.repo.create_insight(
                    user_id=user_id,
                    insight_type=rule["insight_type"],
                    text=rule["high_text"],
                    confidence=rule["confidence_high"],
                    metadata_json={
                        "feature": rule["feature"],
                        "value": feature_value,
                        "threshold_type": "high",
                    },
                )
                insights.append(insight)
            # Low score insights
            elif feature_value < rule["low_threshold"]:
                insight = await self.repo.create_insight(
                    user_id=user_id,
                    insight_type=rule["insight_type"],
                    text=rule["low_text"],
                    confidence=rule["confidence_low"],
                    metadata_json={
                        "feature": rule["feature"],
                        "value": feature_value,
                        "threshold_type": "low",
                    },
                )
                insights.append(insight)

        # Cache the newly generated insights
        if insights:
            await self._cache_insights(user_id, insights)

        return insights

    async def list_insights(
        self,
        user_id: UUID,
        insight_type: Optional[str] = None,
        limit: int = 10,
    ) -> tuple[list, int]:
        """List insights for a user with optional type filter."""
        # Check cache first
        cache_key = f"ai:insights:list:{user_id}:{insight_type or 'all'}"
        if self.redis:
            try:
                cached = await self.redis.get(cache_key)
                if cached:
                    data = json.loads(cached)
                    logger.info(f"Returning cached insights for {user_id}")
                    return data["insights"], data["total"]
            except Exception as e:
                logger.warning(f"Redis cache miss for {cache_key}: {e}")

        # Fetch from DB
        insights, total = await self.repo.list_insights(
            user_id=user_id,
            insight_type=insight_type,
            offset=0,
            limit=limit,
        )

        # Cache the result
        if self.redis and insights:
            try:
                cache_data = {
                    "insights": [
                        {
                            "id": str(i.id),
                            "user_id": str(i.user_id),
                            "insight_type": i.insight_type,
                            "text": i.text,
                            "confidence": i.confidence,
                            "metadata_json": i.metadata_json,
                            "created_at": i.created_at.isoformat(),
                        }
                        for i in insights
                    ],
                    "total": total,
                }
                await self.redis.setex(
                    cache_key, CACHE_TTL_SECONDS, json.dumps(cache_data)
                )
            except Exception as e:
                logger.warning(f"Failed to cache insights: {e}")

        return insights, total

    async def _cache_insights(self, user_id: UUID, insights: list) -> None:
        """Cache newly generated insights."""
        if not self.redis or not insights:
            return

        try:
            cache_key = f"ai:insights:{user_id}"
            cache_data = {
                "insights": [
                    {
                        "id": str(i.id),
                        "user_id": str(i.user_id),
                        "insight_type": i.insight_type,
                        "text": i.text,
                        "confidence": i.confidence,
                        "metadata_json": i.metadata_json,
                        "created_at": i.created_at.isoformat(),
                    }
                    for i in insights
                ],
                "total": len(insights),
            }
            await self.redis.setex(cache_key, CACHE_TTL_SECONDS, json.dumps(cache_data))
            logger.info(f"Cached {len(insights)} insights for {user_id}")
        except Exception as e:
            logger.warning(f"Failed to cache insights: {e}")

    async def invalidate_cache(self, user_id: UUID) -> None:
        """Invalidate cached insights for a user."""
        if not self.redis:
            return

        try:
            pattern = f"ai:insights:{user_id}*"
            cursor = 0
            while True:
                cursor, keys = await self.redis.scan(cursor, match=pattern)
                if keys:
                    await self.redis.delete(*keys)
                if cursor == 0:
                    break
            logger.info(f"Invalidated cached insights for {user_id}")
        except Exception as e:
            logger.warning(f"Failed to invalidate cache: {e}")
