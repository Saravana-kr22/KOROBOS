"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Habit Reminder Worker

Periodic worker that checks which habits are due for reminders based on
scheduled time_of_day and publishes HabitReminderDueEvent to Kafka.
"""

import asyncio
import importlib
from datetime import date, datetime

from backend.shared.database.connection import async_session_factory
from backend.shared.logging.logger import get_logger
from backend.shared.messaging.producer import publish_event
from backend.workers.service_loader import configure_service_app_path

configure_service_app_path("habit-service")
HabitRepository = importlib.import_module("app.repositories.repository").HabitRepository
HabitLogRepository = importlib.import_module(
    "app.repositories.habit_log_repository"
).HabitLogRepository
HabitReminderDueEvent = importlib.import_module(
    "app.events.events"
).HabitReminderDueEvent

logger = get_logger("habit-reminder-worker")


class HabitReminderWorker:
    """
    Periodic worker that:
    1. Checks all HabitSchedule rows where time_of_day matches current minute
    2. Verifies the habit is active and not completed today
    3. Publishes HabitReminderDueEvent to Kafka
    """

    async def run(self):
        """Main worker loop — check every 60 seconds."""
        logger.info("Habit reminder worker started")
        try:
            while True:
                await self._check_and_publish_reminders()
                await asyncio.sleep(60)
        except (KeyboardInterrupt, asyncio.CancelledError):
            logger.info("Habit reminder worker shutting down")

    async def _check_and_publish_reminders(self):
        """Check for reminders due at the current time and publish events."""
        now = datetime.now()
        current_time = now.time().replace(second=0, microsecond=0)
        today = date.today()

        async with async_session_factory() as session:
            log_repo = HabitLogRepository(session)

            # Query all active habits
            # Note: We'll query all habits and filter by schedule in memory
            # since filtering by time_of_day in SQLAlchemy is complex
            from app.models.model import Habit
            from sqlalchemy import select

            stmt = select(Habit).where(Habit.is_active)
            result = await session.execute(stmt)
            habits = result.scalars().all()

            for habit in habits:
                # Get the habit's schedule
                schedule = await log_repo.get_schedule(habit.id)
                if schedule is None or schedule.time_of_day is None:
                    continue  # No reminder scheduled

                # Check if the scheduled time matches the current time
                if schedule.time_of_day != current_time:
                    continue

                # Check if the habit has already been completed today
                completed_today = await log_repo.has_completed_today(habit.id, today)
                if completed_today:
                    continue  # Already completed today

                # Publish reminder event
                try:
                    event = HabitReminderDueEvent(
                        payload={
                            "habit_id": str(habit.id),
                            "user_id": str(habit.user_id),
                            "habit_name": habit.name,
                        }
                    )
                    await publish_event(event, key=str(habit.user_id))
                    logger.info(f"Published reminder for habit {habit.id}")
                except Exception as exc:
                    logger.error(f"Failed to publish reminder event: {exc}")


async def main() -> None:
    worker = HabitReminderWorker()
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
