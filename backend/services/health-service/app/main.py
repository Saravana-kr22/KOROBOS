"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Health Service — health tracking microservice.
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

logger = get_logger("health-service")

# -- Prometheus metrics (Sprint 10 §22) --
# Define metrics BEFORE importing routes to avoid circular imports

MEALS_LOGGED = Counter(
    "meals_logged_total",
    "Total number of meals logged",
    ["service"],
)
WORKOUTS_LOGGED = Counter(
    "workouts_logged_total",
    "Total number of workouts logged",
    ["service"],
)
REQUEST_LATENCY = Histogram(
    "health_request_duration_seconds",
    "HTTP request latency for health endpoints",
    ["method", "endpoint"],
)

# Import router AFTER metrics are defined to avoid circular imports
from app.api.routes import router as api_router  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("Health Service starting up")

    # Kafka producer
    try:
        await get_producer()
        logger.info("Kafka producer initialized")
    except Exception as exc:
        logger.warning(f"Kafka producer not available: {exc}")

    # Shared Redis connection pool
    try:
        app.state.redis = aioredis.from_url(settings.redis_url, decode_responses=True)
        await app.state.redis.ping()
        logger.info("Redis connection pool initialized")
    except Exception as exc:
        logger.warning(f"Redis not available: {exc}")
        app.state.redis = None

    yield

    logger.info("Health Service shutting down")
    await close_producer()
    if app.state.redis:
        await app.state.redis.aclose()


app = FastAPI(
    title="Health Service",
    description="KOROBOS Health Tracking Microservice",
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
    return {"status": "healthy", "service": "health-service"}


@app.get("/metrics")
async def metrics():
    """Prometheus-compatible metrics endpoint (Sprint 10 §22)."""
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

    # Record latency for all routes except /health and /metrics
    if request.url.path not in ["/health", "/metrics"]:
        method = request.method
        endpoint = request.url.path
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(elapsed)

    return response
