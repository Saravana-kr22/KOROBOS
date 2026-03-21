"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Learning Service — learning session tracking microservice.
"""

import time
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from app.config.settings import get_settings
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from backend.shared.logging.logger import get_logger
from backend.shared.messaging.producer import close_producer, get_producer

logger = get_logger("learning-service")

# -- Prometheus metrics --
# Define BEFORE importing routes to avoid circular imports

SESSIONS_CREATED = Counter(
    "learning_sessions_created_total",
    "Total number of learning sessions created",
    ["type"],  # type: manual | timer | topic
)
LEARNING_MINUTES_TOTAL = Counter(
    "learning_minutes_total",
    "Cumulative minutes spent learning across all completed sessions",
)
REQUEST_LATENCY = Histogram(
    "learning_request_duration_seconds",
    "HTTP request latency for learning endpoints",
    ["method", "endpoint"],
)

# Import router AFTER metrics are defined
from app.api.learning_routes import router as api_router  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("Learning Service starting up")

    # Kafka producer
    try:
        await get_producer()
        logger.info("Kafka producer initialized")
    except Exception as exc:
        logger.warning(f"Kafka producer not available: {exc}")

    # Redis connection pool
    try:
        app.state.redis = aioredis.from_url(settings.redis_url, decode_responses=True)
        await app.state.redis.ping()
        logger.info("Redis connection pool initialized")
    except Exception as exc:
        logger.warning(f"Redis not available: {exc}")
        app.state.redis = None

    yield

    logger.info("Learning Service shutting down")
    await close_producer()
    if getattr(app.state, "redis", None):
        await app.state.redis.aclose()


app = FastAPI(
    title="Learning Service",
    description="KOROBOS Learning Session Tracking Microservice",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(api_router)


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
    return {"status": "healthy", "service": "learning-service"}


@app.get("/metrics")
async def metrics():
    """Prometheus-compatible metrics endpoint."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


@app.middleware("http")
async def add_request_latency(request: Request, call_next):
    """Middleware to track request latency for Prometheus."""
    start_time = time.time()
    response = await call_next(request)
    elapsed = time.time() - start_time

    if request.url.path not in ["/health", "/metrics"]:
        REQUEST_LATENCY.labels(
            method=request.method, endpoint=request.url.path
        ).observe(elapsed)

    return response
