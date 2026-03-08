"""
CortexOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Analytics Service — productivity insights microservice.
"""

from contextlib import asynccontextmanager

from app.api.routes import router as api_router
from backend.shared.logging.logger import get_logger
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = get_logger("analytics-service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Analytics Service starting up")
    yield
    logger.info("Analytics Service shutting down")


app = FastAPI(
    title="Analytics Service",
    description="CortexOS Productivity Insights Microservice",
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
