"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Notes Service Prometheus metrics — extracted to avoid circular imports.
"""

from prometheus_client import Counter, Histogram

NOTES_CREATED = Counter(
    "notes_created_total",
    "Total number of notes created",
    ["service"],
)
NOTES_UPDATED = Counter(
    "notes_updated_total",
    "Total number of notes updated",
    ["service"],
)
NOTES_DELETED = Counter(
    "notes_deleted_total",
    "Total number of notes deleted",
    ["service"],
)
REQUEST_LATENCY = Histogram(
    "notes_request_duration_seconds",
    "HTTP request latency for notes endpoints",
    ["method", "endpoint"],
)
