"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Aggregation Service — Cross-domain metrics aggregation and scoring.

Handles:
- Domain-specific metric aggregation (habits, health, learning, knowledge)
- Cross-domain productivity scoring
- Overview computation
"""

import asyncio
from uuid import UUID

from app.services.metrics_engine import MetricsEngine
from sqlalchemy.ext.asyncio import AsyncSession


class AggregationService:
    """Cross-domain aggregation and scoring service."""

    def __init__(self, session: AsyncSession):
        self.metrics = MetricsEngine(session)

    async def get_habit_metrics(self, user_id: UUID) -> dict:
        """Get habit domain metrics (completion rate + current streak)."""
        completion_rate = await self.metrics.get_average_metric(
            user_id, "habit_completion_rate"
        )
        current_streak_obj = await self.metrics.get_latest_metric(
            user_id, "current_streak"
        )
        streak_value = current_streak_obj.value if current_streak_obj else 0
        return {
            "completion_rate": round(completion_rate, 2),
            "current_streak": int(streak_value),
        }

    async def get_health_metrics(self, user_id: UUID) -> dict:
        """Get health domain metrics (intake, burned, balance)."""
        intake = await self.metrics.get_average_metric(user_id, "calorie_intake")
        burned = await self.metrics.get_average_metric(user_id, "calorie_burned")
        return {
            "intake": round(intake, 0),
            "burned": round(burned, 0),
            "balance": round(intake - burned, 0),
        }

    async def get_learning_metrics(self, user_id: UUID) -> dict:
        """Get learning domain metrics."""
        productivity_score = await self.metrics.get_average_metric(
            user_id, "productivity_score"
        )
        consistency = await self.metrics.get_average_metric(
            user_id, "habit_consistency"
        )
        learning = await self.metrics.get_average_metric(user_id, "learning_hours")
        return {
            "productivity_score": round(productivity_score, 2),
            "habit_consistency": round(consistency, 2),
            "learning_hours": round(learning, 2),
        }

    async def get_knowledge_metrics(self, user_id: UUID) -> dict:
        """Get knowledge domain metrics (notes, records)."""
        notes = await self.metrics.get_average_metric(user_id, "notes_created")
        records = await self.metrics.get_average_metric(user_id, "records_created")
        return {
            "notes_created": round(notes, 2),
            "records_created": round(records, 2),
        }

    async def compute_cross_domain_score(self, user_id: UUID) -> int:
        """
        Compute overall productivity score (0-100).

        Formula (Sprint 12):
        score = (habit_score * 0.35) + (learning_score * 0.3) + (health_score * 0.25)
              + (knowledge_score * 0.1)

        Where:
        - habit_score: habit completion rate (0-100)
        - learning_score: learning hours vs 60-min target (0-100)
        - health_score: calorie balance (0-100)
        - knowledge_score: notes + records activity (0-100)
        """
        # Get domain scores in parallel
        (
            habit_completion,
            learning_hours,
            calorie_intake,
            calorie_burned,
            notes_created,
            records_created,
        ) = await asyncio.gather(
            self.metrics.get_average_metric(user_id, "habit_completion_rate"),
            self.metrics.get_average_metric(user_id, "learning_hours"),
            self.metrics.get_average_metric(user_id, "calorie_intake"),
            self.metrics.get_average_metric(user_id, "calorie_burned"),
            self.metrics.get_average_metric(user_id, "notes_created"),
            self.metrics.get_average_metric(user_id, "records_created"),
        )

        # Health score: penalize calorie imbalance
        net_calories = calorie_intake - calorie_burned
        tolerance = 500
        if tolerance == 0:
            health_score = 0.0
        else:
            penalty = (abs(net_calories) / tolerance) * 100.0
            health_score = max(0.0, 100.0 - penalty)

        # Learning score: target 60 minutes/day
        target_minutes = 60
        if target_minutes == 0:
            learning_score = 0.0
        else:
            learning_score = (learning_hours * 60 / target_minutes) * 100.0
            learning_score = min(learning_score, 100.0)

        # Knowledge score: target 2+ items per day (notes or records)
        total_knowledge = notes_created + records_created
        knowledge_score = min((total_knowledge / 2.0) * 100.0, 100.0)

        # Compute weighted score
        score = (
            (habit_completion * 0.35)
            + (learning_score * 0.3)
            + (health_score * 0.25)
            + (knowledge_score * 0.1)
        )
        return max(0, min(100, int(round(score))))

    async def get_consistency_score(self, user_id: UUID) -> dict:
        """
        Compute per-domain consistency scores (0-1).

        Consistency measures how stable/regular activity is within each domain.
        Calculated as: 1.0 - (std_dev / mean), clamped to [0, 1]
        """
        values = await asyncio.gather(
            self.metrics.get_metric_range(user_id, "habit_completion_rate", limit=7),
            self.metrics.get_metric_range(user_id, "learning_hours", limit=7),
            self.metrics.get_metric_range(user_id, "calorie_intake", limit=7),
            self.metrics.get_metric_range(user_id, "notes_created", limit=7),
        )

        consistency = {}
        domains = ["habits", "learning", "health", "knowledge"]

        for domain, metric_values in zip(domains, values):
            if not metric_values or len(metric_values) < 2:
                consistency[domain] = 0.5  # Insufficient data = moderate consistency
                continue

            values_list = [m.value for m in metric_values]
            mean = sum(values_list) / len(values_list)

            if mean == 0:
                consistency[domain] = 0.5
                continue

            variance = sum((x - mean) ** 2 for x in values_list) / len(values_list)
            std_dev = variance**0.5

            # Consistency = 1.0 - normalized std dev, clamped to [0, 1]
            consistency_score = 1.0 - (std_dev / mean if mean > 0 else 0)
            consistency[domain] = max(0.0, min(1.0, round(consistency_score, 2)))

        return consistency

    async def get_overview(self, user_id: UUID) -> dict:
        """Get cross-domain analytics overview."""
        # Fetch all domain metrics in parallel
        (
            productivity_score,
            habits,
            learning,
            health,
            knowledge,
            consistency,
        ) = await asyncio.gather(
            self.compute_cross_domain_score(user_id),
            self.get_habit_metrics(user_id),
            self.get_learning_metrics(user_id),
            self.get_health_metrics(user_id),
            self.get_knowledge_metrics(user_id),
            self.get_consistency_score(user_id),
        )

        return {
            "productivity_score": productivity_score,
            "habits": habits,
            "learning": learning,
            "health": health,
            "knowledge": knowledge,
            "consistency": consistency,
        }
