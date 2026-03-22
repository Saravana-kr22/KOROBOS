"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

AI Service — intelligent recommendations microservice.
"""

from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from app.api.routes import router as api_router
from app.config.settings import get_settings
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from backend.shared.logging.logger import get_logger
from backend.shared.messaging.producer import close_producer, get_producer

logger = get_logger("ai-service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    API Service Lifespan Management

    Note: Insight engines are now managed by a dedicated worker process
    (workers/ai_worker.py) for better scalability and separation of concerns.
    This lifespan handler only manages API-level resources:
    - Kafka producer (for API responses, not event processing)
    - Redis connection pool (for caching)
    """
    logger.info("AI Service (API) starting up")

    settings = get_settings()

    try:
        await get_producer()
        logger.info("Kafka producer initialized")
    except Exception as exc:
        logger.warning(f"Kafka producer not available: {exc}")

    # Initialize Redis connection pool
    try:
        app.state.redis = aioredis.from_url(settings.redis_url, decode_responses=True)
        await app.state.redis.ping()
        logger.info("Redis connection pool initialized")
    except Exception as exc:
        logger.warning(f"Redis not available: {exc}")
        app.state.redis = None

    logger.info("AI Service (API) ready")

    yield

    # Close Redis connection
    if app.state.redis:
        await app.state.redis.aclose()
        logger.info("Redis connection pool closed")

    logger.info("AI Service (API) shutting down")
    await close_producer()


app = FastAPI(
    title="AI Service",
    description="KOROBOS Intelligent Recommendations Microservice",
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
    return {"status": "healthy", "service": "ai-service"}


@app.get("/metrics")
async def metrics():
    return {"status": "success", "data": {"service": "ai-service", "version": "1.0.0"}}
