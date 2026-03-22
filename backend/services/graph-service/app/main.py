"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Graph Service — knowledge graph microservice.
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

logger = get_logger("graph-service")

# -- Prometheus metrics --
NODES_CREATED = Counter(
    "graph_nodes_created_total",
    "Total number of nodes created",
    ["service"],
)
EDGES_CREATED = Counter(
    "graph_edges_created_total",
    "Total number of edges created",
    ["service"],
)
REQUEST_LATENCY = Histogram(
    "graph_request_duration_seconds",
    "HTTP request latency for graph endpoints",
    ["method", "endpoint"],
)
GRAPH_SIZE = Histogram(
    "graph_size_nodes",
    "Number of nodes in user graphs",
    ["user_id"],
)
GRAPH_EDGES_COUNT = Histogram(
    "graph_size_edges",
    "Number of edges in user graphs",
    ["user_id"],
)

# Import router AFTER metrics are defined to avoid circular imports
from app.api.routes import router as api_router  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("Graph Service starting up")

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

    logger.info("Graph Service shutting down")
    await close_producer()
    if app.state.redis:
        await app.state.redis.aclose()


app = FastAPI(
    title="Graph Service",
    description="KOROBOS Knowledge Graph Microservice",
    version="1.0.0",
    lifespan=lifespan,
)

# Standardized: Listen at '/'
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
    return {"status": "healthy", "service": "graph-service"}


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

    # Record latency for all routes except /health and /metrics
    if request.url.path not in ["/health", "/metrics"]:
        method = request.method
        endpoint = request.url.path
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(elapsed)

    return response


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Middleware to implement rate limiting (50 requests/min per user)."""
    # Skip rate limiting for health and metrics endpoints
    if request.url.path in ["/health", "/metrics"]:
        return await call_next(request)

    redis = getattr(request.app.state, "redis", None)
    if not redis:
        return await call_next(request)

    # Extract user_id from X-User-ID header
    user_id = request.headers.get("X-User-ID")
    if not user_id:
        return await call_next(request)

    try:
        # Rate limit key: "ratelimit:user:{user_id}"
        rate_limit_key = f"ratelimit:graph:{user_id}"
        current_count = await redis.incr(rate_limit_key)

        # Set expiry on first request
        if current_count == 1:
            await redis.expire(rate_limit_key, 60)  # 60 seconds window

        # Rate limit: 50 requests per minute
        if current_count > 50:
            return JSONResponse(
                status_code=429,
                content={
                    "status": "error",
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests. Maximum 50 per minute.",
                    },
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = "50"
        response.headers["X-RateLimit-Remaining"] = str(max(0, 50 - current_count))
        return response

    except Exception as exc:
        logger.warning(f"Rate limit check failed: {exc}")
        return await call_next(request)


@app.get("/")
async def root():
    return {"service": "graph-service", "status": "running"}
