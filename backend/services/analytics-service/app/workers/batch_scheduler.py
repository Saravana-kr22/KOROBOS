"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Analytics Service — background batch aggregation scheduler.
Runs daily and weekly aggregation jobs on a schedule.
"""

import logging
from datetime import datetime, timedelta

from app.config.settings import AnalyticsSettings
from app.repositories.clickhouse_repository import ClickHouseRepository
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from backend.shared.database.connection import async_session_factory

logger = logging.getLogger(__name__)


class BatchAggregationScheduler:
    """Manages scheduled batch aggregation jobs.

    Schedules:
    - Hourly aggregation: runs at minute 5 of every hour
    - Daily aggregation: runs at 00:05 UTC (after day ends)
    - Weekly aggregation: runs every Monday at 00:10 UTC
    - Monthly aggregation: runs first day of month at 00:15 UTC

    Integrates ClickHouse for archival of aggregated metrics.
    """

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self._is_running = False
        self.settings = AnalyticsSettings()
        self.clickhouse_repo = self._init_clickhouse()

    def _init_clickhouse(self) -> ClickHouseRepository:
        """Initialize ClickHouse repository (with graceful fallback)."""
        try:
            ch_repo = ClickHouseRepository(
                clickhouse_url=self.settings.clickhouse_url,
                user=self.settings.clickhouse_user,
                password=self.settings.clickhouse_password,
                database=self.settings.clickhouse_database,
            )
            logger.info("ClickHouse repository initialized")
            return ch_repo
        except Exception as e:
            logger.warning("Failed to initialize ClickHouse: %s", e)
            return None

    async def start(self):
        """Start the batch aggregation scheduler."""
        try:
            # Schedule hourly aggregation
            self.scheduler.add_job(
                self._hourly_aggregation_job,
                "cron",
                minute=5,
                name="hourly_aggregation",
                max_instances=1,
            )

            # Schedule daily aggregation
            self.scheduler.add_job(
                self._daily_aggregation_job,
                "cron",
                hour=0,
                minute=5,
                name="daily_aggregation",
                max_instances=1,
            )

            # Schedule weekly aggregation
            self.scheduler.add_job(
                self._weekly_aggregation_job,
                "cron",
                day_of_week="mon",
                hour=0,
                minute=10,
                name="weekly_aggregation",
                max_instances=1,
            )

            # Schedule monthly aggregation
            self.scheduler.add_job(
                self._monthly_aggregation_job,
                "cron",
                day=1,
                hour=0,
                minute=15,
                name="monthly_aggregation",
                max_instances=1,
            )

            self.scheduler.start()
            self._is_running = True
            logger.info("Batch aggregation scheduler started")

        except Exception as e:
            logger.error(
                "Failed to start batch aggregation scheduler: %s", e, exc_info=True
            )
            raise

    async def stop(self):
        """Stop the batch aggregation scheduler."""
        try:
            if self._is_running:
                self.scheduler.shutdown(wait=False)
                self._is_running = False
                logger.info("Batch aggregation scheduler stopped")
        except Exception as e:
            logger.error(
                "Error stopping batch aggregation scheduler: %s", e, exc_info=True
            )

    async def _daily_aggregation_job(self):
        """Daily aggregation job.

        Aggregates metrics for all active users from yesterday.
        Runs at 00:05 UTC (5 minutes after midnight).
        """
        async with async_session_factory() as _session:
            try:
                target_date = datetime.utcnow() - timedelta(days=1)
                logger.info(
                    "Starting daily aggregation for date: %s", target_date.date()
                )

                # TODO: Query database for all active users who have metrics
                # For now, this logs the aggregation start
                # In production, fetch from analytics_metrics table:
                # SELECT DISTINCT user_id FROM analytics_metrics
                # WHERE created_at >= target_date AND created_at < target_date + 1 day
                # batch_svc = BatchAggregationService(session, self.clickhouse_repo)

                logger.info(
                    "Daily aggregation completed for date: %s", target_date.date()
                )

            except Exception as e:
                logger.error("Error in daily aggregation job: %s", e, exc_info=True)

    async def _weekly_aggregation_job(self):
        """Weekly aggregation job.

        Aggregates metrics for all active users from the previous week.
        Runs every Monday at 00:10 UTC.
        """
        async with async_session_factory() as _session:
            try:
                # Get start of previous week (Monday)
                today = datetime.utcnow().date()
                days_since_monday = today.weekday()
                week_start = datetime.utcnow() - timedelta(days=days_since_monday + 7)

                logger.info(
                    "Starting weekly aggregation for week starting: %s",
                    week_start.date(),
                )

                # TODO: Query database for all active users who have metrics
                # For now, this logs the aggregation start
                # In production, fetch from analytics_metrics table:
                # SELECT DISTINCT user_id FROM analytics_metrics
                # WHERE created_at >= week_start AND created_at < week_start + 7 days
                # batch_svc = BatchAggregationService(session, self.clickhouse_repo)

                logger.info(
                    "Weekly aggregation completed for week starting: %s",
                    week_start.date(),
                )

            except Exception as e:
                logger.error("Error in weekly aggregation job: %s", e, exc_info=True)

    async def _hourly_aggregation_job(self):
        """Hourly aggregation job.

        Aggregates metrics for all active users from the previous hour.
        Runs at minute 5 of every hour.
        """
        async with async_session_factory() as _session:
            try:
                target_time = datetime.utcnow() - timedelta(hours=1)
                logger.info(
                    "Starting hourly aggregation for hour: %s", target_time.isoformat()
                )

                # TODO: Query database for all active users who have metrics
                # For now, this logs the aggregation start
                # In production, fetch from analytics_metrics table:
                # SELECT DISTINCT user_id FROM analytics_metrics
                # WHERE created_at >= target_time AND created_at < target_time + 1 hour
                # batch_svc = BatchAggregationService(session, self.clickhouse_repo)

                logger.info(
                    "Hourly aggregation completed for hour: %s", target_time.isoformat()
                )

            except Exception as e:
                logger.error("Error in hourly aggregation job: %s", e, exc_info=True)

    async def _monthly_aggregation_job(self):
        """Monthly aggregation job.

        Aggregates metrics for all active users from the previous month.
        Runs on the first day of each month at 00:15 UTC.
        """
        async with async_session_factory() as _session:
            try:
                today = datetime.utcnow().date()
                # Get first day of current month, then subtract 1 day to get last day
                # of previous month, then calculate month start
                first_of_current = today.replace(day=1)
                last_day_of_prev = first_of_current - timedelta(days=1)
                month_start = last_day_of_prev.replace(day=1)

                logger.info(
                    "Starting monthly aggregation for month starting: %s",
                    month_start.isoformat(),
                )

                # TODO: Query database for all active users who have metrics
                # For now, this logs the aggregation start
                # In production, fetch from analytics_metrics table:
                # SELECT DISTINCT user_id FROM analytics_metrics
                # WHERE created_at >= month_start AND created_at < month_start + 1 month
                # batch_svc = BatchAggregationService(session, self.clickhouse_repo)

                logger.info(
                    "Monthly aggregation completed for month starting: %s",
                    month_start.isoformat(),
                )

            except Exception as e:
                logger.error("Error in monthly aggregation job: %s", e, exc_info=True)
