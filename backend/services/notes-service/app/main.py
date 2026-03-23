"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Notes Service — knowledge management microservice.
"""

from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from app.api.notes_routes import router as api_router
from app.config.settings import get_settings
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from backend.shared.logging.logger import get_logger
from backend.shared.messaging.producer import close_producer, get_producer

logger = get_logger("notes-service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle for the Notes Service."""
    settings = get_settings()
    logger.info("Notes Service starting up")

    # Kafka producer
    try:
        await get_producer()
        logger.info("Kafka producer initialized")
    except Exception as exc:
        logger.warning("Kafka producer not available: %s", exc)

    # Shared Redis connection pool
    try:
        app.state.redis = aioredis.from_url(settings.redis_url, decode_responses=True)
        await app.state.redis.ping()
        logger.info("Redis connection pool initialized")
    except Exception as exc:
        logger.warning("Redis not available: %s", exc)
        app.state.redis = None

    yield

    logger.info("Notes Service shutting down")
    await close_producer()
    if app.state.redis:
        await app.state.redis.aclose()


app = FastAPI(
    title="Notes Service",
    description="KOROBOS Knowledge Management Microservice",
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
    return {"status": "healthy", "service": "notes-service"}


@app.get("/metrics")
async def metrics():
    """Prometheus-compatible metrics endpoint (Sprint 6 §22)."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )
