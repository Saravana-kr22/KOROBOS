"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Recommendation Service — generates actionable recommendations from feature vectors.
"""

import json
from typing import Optional
from uuid import UUID

import redis.asyncio as aioredis
from app.repositories.insight_repository import InsightRepository
from app.services.feature_engineering import FeatureVector
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.logging.logger import get_logger

logger = get_logger("recommendation-service")

# Recommendation generation rules (feature-based)
RECOMMENDATION_RULES = [
    {
        "feature": "habit_consistency_score",
        "category": "habit",
        "low_threshold": 60,
        "low_priority": "high",
        "low_text": (
            "Review your habit schedule for consistency. "
            "Schedule them at a fixed time."
        ),
        "high_threshold": 80,
        "high_priority": "medium",
        "high_text": "Your habit schedule is great — keep it up!",
    },
    {
        "feature": "learning_velocity",
        "category": "learning",
        "low_threshold": 40,
        "low_priority": "high",
        "low_text": "Schedule learning sessions in the morning for better focus.",
        "high_threshold": 70,
        "high_priority": "low",
        "high_text": "Your learning pace is excellent — keep building!",
    },
    {
        "feature": "health_balance_index",
        "category": "health",
        "low_threshold": 50,
        "low_priority": "high",
        "low_text": "Adjust meals to reduce calorie surplus by 200-300 kcal daily.",
        "high_threshold": 80,
        "high_priority": "low",
        "high_text": "Your nutrition is well-balanced — keep up the excellent habits!",
    },
    {
        "feature": "productivity_score",
        "category": "productivity",
        "low_threshold": 50,
        "low_priority": "high",
        "low_text": "Focus on high-impact habits to boost productivity.",
        "high_threshold": 80,
        "high_priority": "low",
        "high_text": "Your productivity is excellent — you are crushing your goals!",
    },
]

# Cache settings
CACHE_TTL_SECONDS = 300  # 5 minutes


class RecommendationService:
    """Service for generating and managing recommendations."""

    def __init__(
        self,
        session: AsyncSession,
        redis: Optional[aioredis.Redis],
        settings,
    ):
        self.repo = InsightRepository(session)
        self.redis = redis
        self.settings = settings

    async def generate_recommendations(
        self, user_id: UUID, feature_vector: FeatureVector
    ) -> list:
        """
        Generate actionable recommendations from feature vector.

        Returns list of AIRecommendation objects.
        """
        recommendations = []

        for rule in RECOMMENDATION_RULES:
            feature_value = getattr(feature_vector, rule["feature"])

            # Low score recommendations (action items)
            if feature_value < rule["low_threshold"]:
                rec = await self.repo.create_recommendation(
                    user_id=user_id,
                    category=rule["category"],
                    text=rule["low_text"],
                    priority=rule["low_priority"],
                    metadata_json={
                        "feature": rule["feature"],
                        "value": feature_value,
                        "threshold_type": "low",
                    },
                )
                recommendations.append(rec)
            # High score recommendations (positive reinforcement)
            elif feature_value >= rule["high_threshold"]:
                rec = await self.repo.create_recommendation(
                    user_id=user_id,
                    category=rule["category"],
                    text=rule["high_text"],
                    priority=rule["high_priority"],
                    metadata_json={
                        "feature": rule["feature"],
                        "value": feature_value,
                        "threshold_type": "high",
                    },
                )
                recommendations.append(rec)

        # Cache the newly generated recommendations
        if recommendations:
            await self._cache_recommendations(user_id, recommendations)

        return recommendations

    async def list_recommendations(
        self,
        user_id: UUID,
        category: Optional[str] = None,
        limit: int = 10,
    ) -> tuple[list, int]:
        """List recommendations for a user with optional category filter."""
        # Check cache first
        cache_key = f"ai:recommendations:list:{user_id}:{category or 'all'}"
        if self.redis:
            try:
                cached = await self.redis.get(cache_key)
                if cached:
                    data = json.loads(cached)
                    logger.info(f"Returning cached recommendations for {user_id}")
                    return data["recommendations"], data["total"]
            except Exception as e:
                logger.warning(f"Redis cache miss for {cache_key}: {e}")

        # Fetch from DB
        recommendations, total = await self.repo.list_recommendations(
            user_id=user_id,
            category=category,
            offset=0,
            limit=limit,
        )

        # Cache the result
        if self.redis and recommendations:
            try:
                cache_data = {
                    "recommendations": [
                        {
                            "id": str(r.id),
                            "user_id": str(r.user_id),
                            "category": r.category,
                            "text": r.text,
                            "priority": r.priority,
                            "metadata_json": r.metadata_json,
                            "created_at": r.created_at.isoformat(),
                        }
                        for r in recommendations
                    ],
                    "total": total,
                }
                await self.redis.setex(
                    cache_key, CACHE_TTL_SECONDS, json.dumps(cache_data)
                )
            except Exception as e:
                logger.warning(f"Failed to cache recommendations: {e}")

        return recommendations, total

    async def _cache_recommendations(
        self, user_id: UUID, recommendations: list
    ) -> None:
        """Cache newly generated recommendations."""
        if not self.redis or not recommendations:
            return

        try:
            cache_key = f"ai:recommendations:{user_id}"
            cache_data = {
                "recommendations": [
                    {
                        "id": str(r.id),
                        "user_id": str(r.user_id),
                        "category": r.category,
                        "text": r.text,
                        "priority": r.priority,
                        "metadata_json": r.metadata_json,
                        "created_at": r.created_at.isoformat(),
                    }
                    for r in recommendations
                ],
                "total": len(recommendations),
            }
            await self.redis.setex(cache_key, CACHE_TTL_SECONDS, json.dumps(cache_data))
            logger.info(f"Cached {len(recommendations)} recommendations for {user_id}")
        except Exception as e:
            logger.warning(f"Failed to cache recommendations: {e}")

    async def invalidate_cache(self, user_id: UUID) -> None:
        """Invalidate cached recommendations for a user."""
        if not self.redis:
            return

        try:
            pattern = f"ai:recommendations:{user_id}*"
            cursor = 0
            while True:
                cursor, keys = await self.redis.scan(cursor, match=pattern)
                if keys:
                    await self.redis.delete(*keys)
                if cursor == 0:
                    break
            logger.info(f"Invalidated cached recommendations for {user_id}")
        except Exception as e:
            logger.warning(f"Failed to invalidate cache: {e}")
