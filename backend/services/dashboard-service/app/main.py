"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Dashboard Service — central intelligence layer microservice.
"""

import time
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from app.config.settings import get_settings
from app.events.event_consumer import DashboardCacheConsumer
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from backend.shared.logging.logger import get_logger
from backend.shared.messaging.producer import close_producer, get_producer

logger = get_logger("dashboard-service")

# -- Prometheus metrics (define BEFORE importing routes) --

DASHBOARD_REQUESTS = Counter(
    "dashboard_requests_total",
    "Total number of dashboard requests",
    ["endpoint"],
)

AGGREGATION_LATENCY = Histogram(
    "dashboard_aggregation_seconds",
    "Time taken to aggregate dashboard data",
    ["method", "endpoint"],
)

CACHE_HITS = Counter(
    "dashboard_cache_hits_total",
    "Total cache hits",
    ["endpoint"],
)

CACHE_MISSES = Counter(
    "dashboard_cache_misses_total",
    "Total cache misses",
    ["endpoint"],
)

# Import router AFTER metrics are defined
from app.api.dashboard_routes import router as api_router  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    settings = get_settings()
    logger.info("Dashboard Service starting up")

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

    # Kafka consumer for cache invalidation
    try:
        consumer = DashboardCacheConsumer(redis=app.state.redis)
        await consumer.start()
        app.state.dashboard_consumer = consumer
        logger.info("Dashboard cache consumer started")
    except Exception as exc:
        logger.warning(f"Dashboard cache consumer not available: {exc}")
        app.state.dashboard_consumer = None

    yield

    logger.info("Dashboard Service shutting down")
    await close_producer()
    if hasattr(app.state, "dashboard_consumer") and app.state.dashboard_consumer:
        await app.state.dashboard_consumer.stop()
    if app.state.redis:
        await app.state.redis.aclose()


app = FastAPI(
    title="Dashboard Service",
    description="KOROBOS Dashboard Aggregation Microservice",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "dashboard-service"}


@app.get("/metrics")
async def metrics():
    """Prometheus-compatible metrics endpoint."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


# Include API router AFTER fixed system routes so /metrics isn't shadowed
app.include_router(api_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
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
        AGGREGATION_LATENCY.labels(method=method, endpoint=endpoint).observe(elapsed)

    return response
