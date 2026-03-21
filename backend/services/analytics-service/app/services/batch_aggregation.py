"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Analytics Service — batch aggregation for periodic rollups.
Computes hourly, daily, and weekly summaries from raw metrics.
"""

import logging
from datetime import datetime, timedelta
from uuid import UUID

from app.repositories.clickhouse_repository import ClickHouseRepository
from app.repositories.repository import AnalyticsRepository
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class BatchAggregationService:
    """Handles batch aggregation of analytics metrics.

    Computes periodic rollups (hourly, daily, weekly) from raw metrics
    for efficient reporting and trend analysis.

    Also pushes aggregated data to ClickHouse for long-term OLAP analysis.
    """

    def __init__(
        self,
        session: AsyncSession,
        clickhouse_repo: ClickHouseRepository = None,
    ):
        self.repo = AnalyticsRepository(session)
        self.session = session
        self.clickhouse = clickhouse_repo

    async def aggregate_daily_summary(self, user_id: UUID, target_date: datetime):
        """Compute daily summary for a user on a specific date.

        Aggregates all metrics recorded on target_date into daily summary:
        - Average habit completion rate
        - Average calorie intake/burned
        - Total learning hours
        - Total notes created
        - Total records created

        Args:
            user_id: User ID
            target_date: Date to aggregate (midnight UTC)
        """
        try:
            start_of_day = target_date.replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            end_of_day = start_of_day + timedelta(days=1)

            # Query metrics from the day
            metrics = await self.repo.get_range_between(
                user_id, start_of_day, end_of_day
            )

            # Group by metric type and compute aggregates
            summary = {
                "date": target_date.date().isoformat(),
                "habit_completion_rate_avg": 0.0,
                "calorie_intake_total": 0.0,
                "calorie_burned_total": 0.0,
                "learning_hours_total": 0.0,
                "notes_created_count": 0,
                "records_created_count": 0,
            }

            metric_groups = {}
            for m in metrics:
                if m.metric_type not in metric_groups:
                    metric_groups[m.metric_type] = []
                metric_groups[m.metric_type].append(m.value)

            # Compute aggregates
            if "habit_completion_rate" in metric_groups:
                rates = metric_groups["habit_completion_rate"]
                summary["habit_completion_rate_avg"] = sum(rates) / len(rates)

            if "calorie_intake" in metric_groups:
                summary["calorie_intake_total"] = sum(metric_groups["calorie_intake"])

            if "calorie_burned" in metric_groups:
                summary["calorie_burned_total"] = sum(metric_groups["calorie_burned"])

            if "learning_hours" in metric_groups:
                summary["learning_hours_total"] = sum(metric_groups["learning_hours"])

            if "notes_created" in metric_groups:
                summary["notes_created_count"] = len(metric_groups["notes_created"])

            if "records_created" in metric_groups:
                summary["records_created_count"] = len(metric_groups["records_created"])

            logger.info(
                "Aggregated daily summary: user_id=%s, date=%s, summary=%s",
                user_id,
                target_date.date(),
                summary,
            )

            # Archive to ClickHouse for long-term analysis
            if self.clickhouse:
                try:
                    metrics_for_ch = {
                        "habit_completion_rate": {
                            "value": summary["habit_completion_rate_avg"],
                            "count": 1,
                            "min": summary["habit_completion_rate_avg"],
                            "max": summary["habit_completion_rate_avg"],
                            "avg": summary["habit_completion_rate_avg"],
                        },
                        "calorie_intake": {
                            "value": summary["calorie_intake_total"],
                            "count": 1,
                            "min": summary["calorie_intake_total"],
                            "max": summary["calorie_intake_total"],
                            "avg": summary["calorie_intake_total"],
                        },
                        "calorie_burned": {
                            "value": summary["calorie_burned_total"],
                            "count": 1,
                            "min": summary["calorie_burned_total"],
                            "max": summary["calorie_burned_total"],
                            "avg": summary["calorie_burned_total"],
                        },
                        "learning_hours": {
                            "value": summary["learning_hours_total"],
                            "count": 1,
                            "min": summary["learning_hours_total"],
                            "max": summary["learning_hours_total"],
                            "avg": summary["learning_hours_total"],
                        },
                        "notes_created": {
                            "value": summary["notes_created_count"],
                            "count": summary["notes_created_count"],
                            "min": 0,
                            "max": summary["notes_created_count"],
                            "avg": summary["notes_created_count"],
                        },
                        "records_created": {
                            "value": summary["records_created_count"],
                            "count": summary["records_created_count"],
                            "min": 0,
                            "max": summary["records_created_count"],
                            "avg": summary["records_created_count"],
                        },
                    }
                    await self.clickhouse.archive_daily_metrics(
                        user_id, target_date, metrics_for_ch
                    )
                    logger.info(
                        "Archived daily metrics to ClickHouse: user_id=%s, date=%s",
                        user_id,
                        target_date.date(),
                    )
                except Exception as ch_error:
                    logger.warning(
                        "Failed to archive daily metrics to ClickHouse: %s", ch_error
                    )

            return summary

        except Exception as e:
            logger.error(
                "Error aggregating daily summary: user_id=%s, date=%s, error=%s",
                user_id,
                target_date,
                e,
                exc_info=True,
            )
            raise

    async def aggregate_weekly_summary(self, user_id: UUID, week_start: datetime):
        """Compute weekly summary for a user.

        Aggregates 7 days of metrics into weekly summary:
        - Average habit completion rate
        - Average calorie balance
        - Total learning hours
        - Average daily notes
        - Average daily records

        Args:
            user_id: User ID
            week_start: Start of week (Monday, midnight UTC)
        """
        try:
            week_end = week_start + timedelta(days=7)

            # Query metrics from the week
            metrics = await self.repo.get_range_between(user_id, week_start, week_end)

            # Group by metric type
            metric_groups = {}
            for m in metrics:
                if m.metric_type not in metric_groups:
                    metric_groups[m.metric_type] = []
                metric_groups[m.metric_type].append(m.value)

            # Compute weekly aggregates
            summary = {
                "week_start": week_start.date().isoformat(),
                "week_end": (week_end - timedelta(days=1)).date().isoformat(),
                "habit_completion_rate_avg": 0.0,
                "calorie_balance_avg": 0.0,
                "learning_hours_total": 0.0,
                "notes_created_total": 0,
                "records_created_total": 0,
            }

            if "habit_completion_rate" in metric_groups:
                rates = metric_groups["habit_completion_rate"]
                summary["habit_completion_rate_avg"] = sum(rates) / len(rates)

            if "calorie_intake" in metric_groups and "calorie_burned" in metric_groups:
                intake = sum(metric_groups["calorie_intake"])
                burned = sum(metric_groups["calorie_burned"])
                summary["calorie_balance_avg"] = intake - burned

            if "learning_hours" in metric_groups:
                summary["learning_hours_total"] = sum(metric_groups["learning_hours"])

            if "notes_created" in metric_groups:
                summary["notes_created_total"] = len(metric_groups["notes_created"])

            if "records_created" in metric_groups:
                summary["records_created_total"] = len(metric_groups["records_created"])

            logger.info(
                "Aggregated weekly summary: user_id=%s, week_start=%s, summary=%s",
                user_id,
                week_start.date(),
                summary,
            )

            return summary

        except Exception as e:
            logger.error(
                "Error aggregating weekly summary: user_id=%s, week_start=%s, error=%s",
                user_id,
                week_start,
                e,
                exc_info=True,
            )
            raise
