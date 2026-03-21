"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

AI Service — intelligent recommendations microservice.
"""

import asyncio
from contextlib import asynccontextmanager

from app.api.routes import router as api_router
from app.events.learning_insight_engine import LearningInsightEngine
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from backend.shared.logging.logger import get_logger
from backend.shared.messaging.producer import close_producer, get_producer

logger = get_logger("ai-service")

# Global insight engine instance for lifespan management
_learning_insight_engine: LearningInsightEngine | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _learning_insight_engine
    logger.info("AI Service starting up")

    try:
        await get_producer()
        logger.info("Kafka producer initialized")
    except Exception as exc:
        logger.warning(f"Kafka producer not available: {exc}")

    # Start learning insight engine
    try:
        _learning_insight_engine = LearningInsightEngine()
        asyncio.create_task(_learning_insight_engine.start())
        logger.info("Learning insight engine started")
    except Exception as exc:
        logger.warning("Learning insight engine failed to start: %s", exc)
        _learning_insight_engine = None

    yield

    # Stop learning insight engine
    if _learning_insight_engine:
        try:
            await _learning_insight_engine.stop()
            logger.info("Learning insight engine stopped")
        except Exception as exc:
            logger.warning("Error stopping learning insight engine: %s", exc)

    logger.info("AI Service shutting down")
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
