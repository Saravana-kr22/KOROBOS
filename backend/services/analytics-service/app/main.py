"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Analytics Service — productivity insights microservice.
"""

import asyncio
from contextlib import asynccontextmanager

from app.api.routes import router as api_router
from app.events.learning_consumer import LearningEventConsumer
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from backend.shared.logging.logger import get_logger
from backend.shared.messaging.producer import close_producer, get_producer

logger = get_logger("analytics-service")

# Global consumer instance for lifespan management
_learning_consumer: LearningEventConsumer | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _learning_consumer
    logger.info("Analytics Service starting up")

    try:
        await get_producer()
    except Exception as exc:
        logger.warning("Kafka producer unavailable: %s", exc)

    # Start learning event consumer
    try:
        _learning_consumer = LearningEventConsumer()
        asyncio.create_task(_learning_consumer.start())
        logger.info("Learning event consumer started")
    except Exception as exc:
        logger.warning("Learning event consumer failed to start: %s", exc)
        _learning_consumer = None

    yield

    # Stop learning event consumer
    if _learning_consumer:
        try:
            await _learning_consumer.stop()
            logger.info("Learning event consumer stopped")
        except Exception as exc:
            logger.warning("Error stopping learning event consumer: %s", exc)

    await close_producer()
    logger.info("Analytics Service shutting down")


app = FastAPI(
    title="Analytics Service",
    description="KOROBOS Productivity Insights Microservice",
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
    return {"status": "healthy", "service": "analytics-service"}


@app.get("/metrics")
async def metrics():
    return {
        "status": "success",
        "data": {"service": "analytics-service", "version": "1.0.0"},
    }
