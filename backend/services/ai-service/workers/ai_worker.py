"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

AI Service Worker — manages insight engines as a dedicated background process.

This worker can be run independently of the main API service:
    python -m backend.services.ai_service.workers.ai_worker

It manages:
    - LearningInsightEngine: Processes learning.session.completed events
    - HabitInsightEngine: Processes habit.completed events
    - HealthInsightEngine: Processes meal.logged, workout.logged events
    - NoteInsightEngine: Processes note.created events

Benefits of separation:
    - API service remains lightweight and responsive
    - Insight engines can scale independently
    - Easier to monitor and control event processing
    - Can be deployed as a separate container/service
"""

import asyncio
import sys
from pathlib import Path

# Add the ai-service to sys.path for imports
ai_service_path = Path(__file__).parent.parent
sys.path.insert(0, str(ai_service_path))

# noqa: E402 — imports below require sys.path modification above
from app.events.habit_insight_engine import HabitInsightEngine  # noqa: E402
from app.events.health_insight_engine import HealthInsightEngine  # noqa: E402
from app.events.learning_insight_engine import LearningInsightEngine  # noqa: E402
from app.events.note_insight_engine import NoteInsightEngine  # noqa: E402

from backend.shared.logging.logger import get_logger  # noqa: E402
from backend.shared.messaging.producer import close_producer, get_producer  # noqa: E402

logger = get_logger("ai-worker")

# Global engine instances
_engines = []


async def start_engines():
    """Initialize and start all insight engines."""
    global _engines

    engines_config = [
        ("Learning", LearningInsightEngine),
        ("Habit", HabitInsightEngine),
        ("Health", HealthInsightEngine),
        ("Note", NoteInsightEngine),
    ]

    for name, EngineClass in engines_config:
        try:
            engine = EngineClass()
            asyncio.create_task(engine.start())
            _engines.append((name, engine))
            logger.info(f"{name} Insight Engine started")
        except Exception as exc:
            logger.warning(f"{name} Insight Engine failed to start: {exc}")


async def stop_engines():
    """Stop all running insight engines."""
    global _engines

    for name, engine in _engines:
        try:
            await engine.stop()
            logger.info(f"{name} Insight Engine stopped")
        except Exception as exc:
            logger.warning(f"Error stopping {name} Insight Engine: {exc}")

    _engines.clear()


async def main() -> None:
    """Main entry point for the AI worker."""
    logger.info("AI Worker starting up")

    # Initialize Kafka producer
    try:
        await get_producer()
        logger.info("Kafka producer initialized")
    except Exception as exc:
        logger.warning(f"Kafka producer not available: {exc}")

    # Start all insight engines
    await start_engines()

    logger.info("AI Worker ready — listening for events")
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("AI Worker shutting down")
        await stop_engines()
        await close_producer()


if __name__ == "__main__":
    asyncio.run(main())
