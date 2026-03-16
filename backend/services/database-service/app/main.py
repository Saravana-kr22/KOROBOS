"""
KOROBOS — Database Service

FastAPI application for the structured database system.
"""

from contextlib import asynccontextmanager
from typing import Any

import aioredis
from fastapi import FastAPI, Request
from prometheus_client import Counter, Histogram, generate_latest
from starlette.responses import JSONResponse, Response

from backend.services.database_service.app.api.database_routes import router
from backend.services.database_service.app.config.settings import get_settings
from backend.shared.logging.logger import get_logger
from backend.shared.messaging.producer import close_producer, get_producer

logger = get_logger(__name__)

# ============================================================================
# Prometheus Metrics
# ============================================================================

databases_created_total = Counter(
    "databases_created_total",
    "Total number of databases created",
)
records_created_total = Counter(
    "records_created_total",
    "Total number of records created",
)
records_updated_total = Counter(
    "records_updated_total",
    "Total number of records updated",
)
records_deleted_total = Counter(
    "records_deleted_total",
    "Total number of records deleted",
)
db_query_duration_seconds = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0),
)


# ============================================================================
# Lifespan
# ============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle management.

    Initializes:
      - Kafka producer
      - Redis connection pool

    Cleans up:
      - Kafka producer
      - Redis connection
    """
    logger.info("Database Service starting up")

    # Initialize Kafka producer
    try:
        await get_producer()
        logger.info("Kafka producer initialized")
    except Exception as exc:
        logger.warning(f"Kafka producer initialization failed: {exc}")

    # Initialize Redis
    try:
        settings = get_settings()
        app.state.redis = await aioredis.from_url(
            settings.redis_url,
            encoding="utf8",
            decode_responses=True,
        )
        logger.info("Redis connection pool initialized")
    except Exception as exc:
        logger.warning(f"Redis initialization failed: {exc}")
        app.state.redis = None

    yield

    # Shutdown
    logger.info("Database Service shutting down")
    await close_producer()
    if app.state.redis:
        await app.state.redis.close()


# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(
    title="KOROBOS Database Service",
    description="Structured database system with dynamic properties and views",
    version="1.0.0",
    lifespan=lifespan,
)

# Include routes
app.include_router(router)


# ============================================================================
# Exception Handler
# ============================================================================


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler.

    Logs exceptions and returns standardized error response.
    """
    logger.error(
        f"Unhandled exception: {exc}",
        exc_info=True,
        extra={"path": request.url.path},
    )

    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error": {
                "message": "Internal server error",
                "code": "INTERNAL_SERVER_ERROR",
            },
        },
    )


# ============================================================================
# Health and Metrics
# ============================================================================


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, Any]:
    """Health check endpoint.

    Returns:
        Health status with service name
    """
    return {
        "status": "healthy",
        "service": "database-service",
    }


@app.get("/metrics", tags=["Monitoring"])
async def metrics() -> Response:
    """Prometheus metrics endpoint.

    Returns:
        Prometheus-formatted metrics
    """
    return Response(
        generate_latest(),
        media_type="text/plain",
    )


# ============================================================================
# Request Logging Middleware
# ============================================================================


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests and responses."""
    method = request.method
    path = request.url.path

    response = await call_next(request)

    logger.debug(
        f"{method} {path} {response.status_code}",
    )

    return response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )
