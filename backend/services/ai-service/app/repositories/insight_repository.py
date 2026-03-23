"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Repository for AI Insights and Recommendations.
"""

from typing import Optional
from uuid import UUID

from app.models.insight_model import AIInsight, AIRecommendation
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession


class InsightRepository:
    """Repository for AI Insights and Recommendations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # --- Insights ---

    async def create_insight(
        self,
        user_id: UUID,
        insight_type: str,
        text: str,
        confidence: float = 1.0,
        metadata_json: dict = None,
    ) -> AIInsight:
        """Create a new insight."""
        obj = AIInsight(
            user_id=user_id,
            insight_type=insight_type,
            text=text,
            confidence=confidence,
            metadata_json=metadata_json or {},
        )
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def get_insight_by_id(self, insight_id: UUID) -> Optional[AIInsight]:
        """Get insight by ID."""
        result = await self.session.execute(
            select(AIInsight).where(AIInsight.id == insight_id)
        )
        return result.scalar_one_or_none()

    async def list_insights(
        self,
        user_id: UUID,
        insight_type: Optional[str] = None,
        offset: int = 0,
        limit: int = 10,
    ) -> tuple[list[AIInsight], int]:
        """List insights for a user with optional type filter."""
        filters = [AIInsight.user_id == user_id]
        if insight_type:
            filters.append(AIInsight.insight_type == insight_type)

        count_q = select(func.count()).select_from(AIInsight).where(and_(*filters))
        total = (await self.session.execute(count_q)).scalar_one()

        q = (
            select(AIInsight)
            .where(and_(*filters))
            .order_by(AIInsight.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(q)
        return list(result.scalars().all()), total

    async def delete_insight(self, insight: AIInsight) -> None:
        """Delete an insight."""
        await self.session.delete(insight)
        await self.session.flush()

    # --- Recommendations ---

    async def create_recommendation(
        self,
        user_id: UUID,
        category: str,
        text: str,
        priority: str = "medium",
        metadata_json: dict = None,
    ) -> AIRecommendation:
        """Create a new recommendation."""
        obj = AIRecommendation(
            user_id=user_id,
            category=category,
            text=text,
            priority=priority,
            metadata_json=metadata_json or {},
        )
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def get_recommendation_by_id(
        self, recommendation_id: UUID
    ) -> Optional[AIRecommendation]:
        """Get recommendation by ID."""
        result = await self.session.execute(
            select(AIRecommendation).where(AIRecommendation.id == recommendation_id)
        )
        return result.scalar_one_or_none()

    async def list_recommendations(
        self,
        user_id: UUID,
        category: Optional[str] = None,
        offset: int = 0,
        limit: int = 10,
    ) -> tuple[list[AIRecommendation], int]:
        """List recommendations for a user with optional category filter."""
        filters = [AIRecommendation.user_id == user_id]
        if category:
            filters.append(AIRecommendation.category == category)

        count_q = (
            select(func.count()).select_from(AIRecommendation).where(and_(*filters))
        )
        total = (await self.session.execute(count_q)).scalar_one()

        q = (
            select(AIRecommendation)
            .where(and_(*filters))
            .order_by(AIRecommendation.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(q)
        return list(result.scalars().all()), total

    async def delete_recommendation(self, recommendation: AIRecommendation) -> None:
        """Delete a recommendation."""
        await self.session.delete(recommendation)
        await self.session.flush()
