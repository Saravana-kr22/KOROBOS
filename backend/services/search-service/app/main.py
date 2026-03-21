"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Search Service — unified search across all domains.
"""

from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from app.api.search_routes import router as api_router
from app.config.settings import get_settings
from app.services.indexing_service import IndexingService
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from backend.shared.logging.logger import get_logger

logger = get_logger("search-service")

# ── Prometheus metrics ──

SEARCH_QUERIES_TOTAL = Counter(
    "search_queries_total",
    "Total number of search queries",
    ["service", "endpoint"],
)
SEARCH_LATENCY_SECONDS = Histogram(
    "search_latency_seconds",
    "Search query latency in seconds",
    ["service", "endpoint"],
)
SUGGEST_QUERIES_TOTAL = Counter(
    "suggest_queries_total",
    "Total number of suggest queries",
    ["service"],
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle for the Search Service."""
    settings = get_settings()
    logger.info("Search Service starting up")

    # Redis connection pool (required)
    try:
        app.state.redis = aioredis.from_url(settings.redis_url, decode_responses=True)
        await app.state.redis.ping()
        logger.info("Redis connection pool initialized")
    except Exception as exc:
        logger.warning("Redis not available: %s", exc)
        app.state.redis = None

    # Search configuration
    app.state.search_url = settings.search_url
    app.state.search_api_key = settings.search_api_key

    # Initialize Meilisearch index settings
    try:
        indexing_service = IndexingService(
            search_url=settings.search_url,
            search_api_key=settings.search_api_key,
        )
        await indexing_service.initialize_indexes()
        logger.info("Meilisearch indexes initialized")
    except Exception as exc:
        logger.warning("Index initialization failed (non-fatal): %s", exc)

    yield

    logger.info("Search Service shutting down")
    if app.state.redis:
        await app.state.redis.aclose()


app = FastAPI(
    title="Search Service",
    description="KOROBOS Unified Search Microservice",
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
    return {"status": "healthy", "service": "search-service"}


@app.get("/metrics")
async def metrics():
    """Prometheus-compatible metrics endpoint."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )
