"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Prometheus metrics instrumentation for analytics service.
Tracks: processing latency, event throughput, API latency, database latency.
"""

import time
from typing import Callable

from prometheus_client import CollectorRegistry, Counter, Histogram
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Create metrics registry
metrics_registry = CollectorRegistry()

# Request/API metrics
http_request_duration = Histogram(
    name="analytics_http_request_duration_ms",
    documentation="HTTP request latency in milliseconds",
    labelnames=["method", "endpoint", "status"],
    registry=metrics_registry,
    buckets=(10, 50, 100, 250, 500, 1000, 2500, 5000),
)

http_request_count = Counter(
    name="analytics_http_requests_total",
    documentation="Total HTTP requests",
    labelnames=["method", "endpoint", "status"],
    registry=metrics_registry,
)

# Processing/Event metrics
event_processing_latency = Histogram(
    name="analytics_event_processing_latency_ms",
    documentation="Event processing latency in milliseconds",
    labelnames=["event_type", "consumer"],
    registry=metrics_registry,
    buckets=(10, 50, 100, 250, 500, 1000),
)

event_processing_count = Counter(
    name="analytics_events_processed_total",
    documentation="Total events processed",
    labelnames=["event_type", "consumer", "status"],
    registry=metrics_registry,
)

# Database metrics
db_query_latency = Histogram(
    name="analytics_db_query_latency_ms",
    documentation="Database query latency in milliseconds",
    labelnames=["query_type", "duration"],
    registry=metrics_registry,
    buckets=(5, 10, 25, 50, 100, 250, 500, 1000),
)

db_query_count = Counter(
    name="analytics_db_queries_total",
    documentation="Total database queries",
    labelnames=["query_type", "status"],
    registry=metrics_registry,
)

# Caching metrics
cache_hits = Counter(
    name="analytics_cache_hits_total",
    documentation="Total cache hits",
    labelnames=["cache_key"],
    registry=metrics_registry,
)

cache_misses = Counter(
    name="analytics_cache_misses_total",
    documentation="Total cache misses",
    labelnames=["cache_key"],
    registry=metrics_registry,
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to track HTTP request latency and count."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Record metrics for each HTTP request."""
        start_time = time.time()
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000

        # Extract endpoint path
        endpoint = request.url.path.replace("/analytics", "")
        if not endpoint:
            endpoint = "/"

        # Record metrics
        http_request_duration.labels(
            method=request.method,
            endpoint=endpoint,
            status=response.status_code,
        ).observe(duration_ms)

        http_request_count.labels(
            method=request.method,
            endpoint=endpoint,
            status=response.status_code,
        ).inc()

        return response


def record_event_processing(
    event_type: str, consumer_name: str, duration_ms: float, success: bool
):
    """Record event processing metrics."""
    event_processing_latency.labels(
        event_type=event_type,
        consumer=consumer_name,
    ).observe(duration_ms)

    event_processing_count.labels(
        event_type=event_type,
        consumer=consumer_name,
        status="success" if success else "error",
    ).inc()


def record_db_query(query_type: str, duration_ms: float, success: bool):
    """Record database query metrics."""
    db_query_latency.labels(
        query_type=query_type,
        duration=_categorize_duration(duration_ms),
    ).observe(duration_ms)

    db_query_count.labels(
        query_type=query_type,
        status="success" if success else "error",
    ).inc()


def record_cache_hit(cache_key: str):
    """Record cache hit."""
    cache_hits.labels(cache_key=cache_key).inc()


def record_cache_miss(cache_key: str):
    """Record cache miss."""
    cache_misses.labels(cache_key=cache_key).inc()


def _categorize_duration(duration_ms: float) -> str:
    """Categorize query duration."""
    if duration_ms < 10:
        return "fast"
    elif duration_ms < 100:
        return "normal"
    elif duration_ms < 500:
        return "slow"
    else:
        return "very_slow"
