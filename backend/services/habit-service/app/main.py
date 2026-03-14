"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Habit Service — habit tracking microservice.
"""

from contextlib import asynccontextmanager

from app.api.routes import router as api_router
from backend.shared.logging.logger import get_logger
from backend.shared.messaging.producer import close_producer, get_producer
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = get_logger("habit-service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Habit Service starting up")
    try:
        await get_producer()
        logger.info("Kafka producer initialized")
    except Exception as exc:
        logger.warning(f"Kafka producer not available: {exc}")
    yield
    logger.info("Habit Service shutting down")
    await close_producer()


app = FastAPI(
    title="Habit Service",
    description="KOROBOS Habit Tracking Microservice",
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
    return {"status": "healthy", "service": "habit-service"}


@app.get("/metrics")
async def metrics():
    return {
        "status": "success",
        "data": {"service": "habit-service", "version": "1.0.0"},
    }
