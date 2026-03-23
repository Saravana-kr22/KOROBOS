"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Test configuration for Analytics Service tests.
"""

import os
import sys

# Add the analytics-service root to sys.path so `app.*` imports resolve
_SERVICE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _SERVICE_ROOT not in sys.path:
    sys.path.insert(0, _SERVICE_ROOT)

# Set test environment variables
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("JWT_SECRET", "test-secret-key")
os.environ.setdefault("SERVICE_NAME", "analytics-service-test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("CLICKHOUSE_HOST", "localhost")
os.environ.setdefault("CLICKHOUSE_PORT", "9000")
os.environ.setdefault("CLICKHOUSE_DB", "korobos")
