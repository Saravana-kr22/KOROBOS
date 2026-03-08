"""
CortexOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

API Gateway — single entry point for all CortexOS client requests.

Responsibilities:
  - Request routing to microservices
  - JWT authentication validation
  - Rate limiting (Redis-backed)
  - Structured request logging
  - API versioning (/api/v1/*)
  - OpenAPI documentation
  - CORS support
"""

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from app.config.gateway_settings import get_gateway_settings
from app.middleware.auth_middleware import AuthMiddleware
from app.middleware.logging_middleware import LoggingMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.router import api_router
from app.services.service_registry import ServiceRegistry

from backend.shared.logging.logger import get_logger

# -- Logging setup --

logger = get_logger("api-gateway")

# -- Prometheus-style counters --

_request_count: dict[str, int] = {}
_error_count: dict[str, int] = {}
_latency_sum: dict[str, float] = {}


# -- Lifespan --

_redis_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle for the API Gateway."""
    global _redis_client
    settings = get_gateway_settings()

    # Startup: connect Redis for rate limiting
    try:
        import redis.asyncio as aioredis

        _redis_client = aioredis.from_url(
            settings.redis_url, decode_responses=True
        )
        await _redis_client.ping()
        logger.info("Redis connected for rate limiting")
    except Exception as exc:
        logger.warning(f"Redis not available — rate limiting disabled: {exc}")
        _redis_client = None

    # Log registered services
    registry = ServiceRegistry()
    for name, url in registry.list_services().items():
        logger.info(f"Service registered: {name} → {url}")

    yield

    # Shutdown: close Redis
    if _redis_client:
        await _redis_client.close()
        logger.info("Redis connection closed")


# -- App Factory --

app = FastAPI(
    title="CortexOS API Gateway",
    description="Single entry point for all CortexOS microservice requests",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# -- CORS (configurable via GatewaySettings) --

_settings = get_gateway_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -- Middleware Stack (order matters: outermost runs first) --
# 1. Logging -> 2. Rate Limit -> 3. Auth

app.add_middleware(AuthMiddleware)
app.add_middleware(RateLimitMiddleware, redis_client=_redis_client)
app.add_middleware(LoggingMiddleware)

# -- Routes --

app.include_router(api_router)


# -- Health & Metrics --


@app.get("/health", tags=["System"])
async def health():
    """Health check endpoint for Kubernetes probes."""
    return {"status": "healthy", "service": "api-gateway"}


@app.get("/metrics", tags=["System"])
async def metrics():
    """Service metrics in JSON format."""
    registry = ServiceRegistry()
    return {
        "status": "success",
        "data": {
            "service": "api-gateway",
            "version": "1.0.0",
            "registered_services": list(registry.list_services().keys()),
            "request_counts": dict(_request_count),
            "error_counts": dict(_error_count),
        },
    }


@app.get("/metrics/prometheus", tags=["System"], response_class=PlainTextResponse)
async def prometheus_metrics():
    """Prometheus-compatible exposition format."""
    lines = [
        "# HELP cortexos_gateway_requests_total Total number of requests",
        "# TYPE cortexos_gateway_requests_total counter",
    ]
    for path, count in _request_count.items():
        safe = path.replace('"', '').replace('\\', '')
        lines.append(f'cortexos_gateway_requests_total{{path="{safe}"}} {count}')

    lines.append("# HELP cortexos_gateway_errors_total Total number of error responses")
    lines.append("# TYPE cortexos_gateway_errors_total counter")
    for path, count in _error_count.items():
        safe = path.replace('"', '').replace('\\', '')
        lines.append(f'cortexos_gateway_errors_total{{path="{safe}"}} {count}')

    lines.append("# HELP cortexos_gateway_latency_seconds_total Cumulative latency")
    lines.append("# TYPE cortexos_gateway_latency_seconds_total counter")
    for path, total in _latency_sum.items():
        safe = path.replace('"', '').replace('\\', '')
        metric = f'cortexos_gateway_latency_seconds_total{{path="{safe}"}}'
        lines.append(f"{metric} {total:.4f}")

    return "\n".join(lines) + "\n"


@app.middleware("http")
async def collect_prometheus_metrics(request: Request, call_next):
    """Collect basic request metrics for Prometheus."""
    path = request.url.path
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start

    _request_count[path] = _request_count.get(path, 0) + 1
    _latency_sum[path] = _latency_sum.get(path, 0.0) + duration
    if response.status_code >= 400:
        _error_count[path] = _error_count.get(path, 0) + 1

    return response
