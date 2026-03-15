"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Auth Service — authentication and user identity microservice.
"""

from contextlib import asynccontextmanager

from app.api.routes import router as api_router
from app.middleware.rate_limit import add_rate_limit_middleware
from app.services.metrics import get_metrics_summary, get_prometheus_metrics
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse

from backend.shared.logging.logger import get_logger
from backend.shared.messaging.producer import close_producer, get_producer

logger = get_logger("auth-service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Auth Service starting up")
    try:
        await get_producer()
        logger.info("Kafka producer initialized")
    except Exception as exc:
        logger.warning(f"Kafka producer not available: {exc}")
    yield
    logger.info("Auth Service shutting down")
    await close_producer()


app = FastAPI(
    title="Auth Service",
    description="KOROBOS Authentication Microservice",
    version="1.0.0",
    lifespan=lifespan,
)

# Add rate limiting middleware
add_rate_limit_middleware(app)

# Standardized: Services listen at '/' and let the gateway
# handle '/api/v1/{service_name}'
app.include_router(api_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
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
    return {"status": "healthy", "service": "auth-service"}


@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """Auth service metrics in JSON format."""
    return {
        "status": "success",
        "data": {
            "service": "auth-service",
            "version": "1.0.0",
            "metrics": get_metrics_summary(),
        },
    }


@app.get("/metrics/prometheus", tags=["Monitoring"], response_class=PlainTextResponse)
async def prometheus_metrics():
    """Prometheus-compatible metrics exposition format."""
    return get_prometheus_metrics()
