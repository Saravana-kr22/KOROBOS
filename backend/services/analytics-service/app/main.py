"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Analytics Service — productivity insights microservice.
"""

import asyncio
from contextlib import asynccontextmanager

import redis
from app.api.routes import router as api_router
from app.events.database_consumer import DatabaseEventConsumer
from app.events.habit_consumer import HabitEventConsumer
from app.events.health_consumer import HealthEventConsumer
from app.events.learning_consumer import LearningEventConsumer
from app.events.notes_consumer import NotesEventConsumer
from app.middleware.metrics import MetricsMiddleware, metrics_registry
from app.middleware.rate_limiter import RedisRateLimiter, rate_limit_middleware
from app.workers.batch_scheduler import BatchAggregationScheduler
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from backend.shared.logging.logger import get_logger
from backend.shared.messaging.producer import close_producer, get_producer

logger = get_logger("analytics-service")

# Global consumer instances for lifespan management
_consumers: list = []
_batch_scheduler: BatchAggregationScheduler | None = None
_redis_client: redis.Redis | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _consumers, _batch_scheduler, _redis_client
    logger.info("Analytics Service starting up")

    # Initialize Redis for rate limiting
    try:
        _redis_client = redis.Redis(
            host="localhost", port=6379, db=0, decode_responses=True
        )
        _redis_client.ping()
        app.state.rate_limiter = RedisRateLimiter(
            _redis_client, requests_per_minute=100
        )
        logger.info("Redis and rate limiter initialized")
    except Exception as exc:
        logger.warning("Failed to initialize rate limiter: %s", exc)

    try:
        await get_producer()
    except Exception as exc:
        logger.warning("Kafka producer unavailable: %s", exc)

    # Start all event consumers
    consumer_classes = [
        LearningEventConsumer(),
        HabitEventConsumer(),
        HealthEventConsumer(),
        NotesEventConsumer(),
        DatabaseEventConsumer(),
    ]

    for consumer in consumer_classes:
        try:
            asyncio.create_task(consumer.start())
            _consumers.append(consumer)
            logger.info("Started event consumer: %s", consumer.__class__.__name__)
        except Exception as exc:
            logger.warning(
                "Event consumer %s failed to start: %s",
                consumer.__class__.__name__,
                exc,
            )

    # Start batch aggregation scheduler
    try:
        _batch_scheduler = BatchAggregationScheduler()
        await _batch_scheduler.start()
        logger.info("Batch aggregation scheduler started")
    except Exception as exc:
        logger.warning("Batch aggregation scheduler failed to start: %s", exc)
        _batch_scheduler = None

    yield

    # Stop batch aggregation scheduler
    if _batch_scheduler:
        try:
            await _batch_scheduler.stop()
            logger.info("Batch aggregation scheduler stopped")
        except Exception as exc:
            logger.warning("Error stopping batch aggregation scheduler: %s", exc)

    # Stop all event consumers
    for consumer in _consumers:
        try:
            await consumer.stop()
            logger.info("Stopped event consumer: %s", consumer.__class__.__name__)
        except Exception as exc:
            logger.warning(
                "Error stopping event consumer %s: %s",
                consumer.__class__.__name__,
                exc,
            )

    # Close Redis connection
    if _redis_client:
        try:
            _redis_client.close()
            logger.info("Redis connection closed")
        except Exception as exc:
            logger.warning("Error closing Redis connection: %s", exc)

    await close_producer()
    logger.info("Analytics Service shutting down")


app = FastAPI(
    title="Analytics Service",
    description="KOROBOS Productivity Insights Microservice",
    version="1.0.0",
    lifespan=lifespan,
)

# Add middleware in reverse order (innermost first)
app.add_middleware(MetricsMiddleware)
app.add_middleware(rate_limit_middleware)

app.include_router(api_router, prefix="/analytics")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
            },
        },
    )


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "analytics-service"}


@app.get("/metrics")
async def metrics_endpoint():
    """Prometheus metrics endpoint."""
    return Response(
        content=generate_latest(metrics_registry),
        media_type=CONTENT_TYPE_LATEST,
    )
