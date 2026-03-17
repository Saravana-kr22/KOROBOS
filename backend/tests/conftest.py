"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Pytest configuration and fixtures for backend tests.
"""

import os
import sys

# Add the project root and gateway app to the Python path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
GATEWAY_APP = os.path.join(BACKEND_ROOT, "gateway", "api-gateway")
HABIT_SERVICE_APP = os.path.join(BACKEND_ROOT, "services", "habit-service")

# Add paths: GATEWAY_APP first (highest priority), then others
# insert(0) adds to front, so last insertion ends up at index 0
for path in [PROJECT_ROOT, BACKEND_ROOT, HABIT_SERVICE_APP, GATEWAY_APP]:
    if path and path not in sys.path:
        sys.path.insert(0, path)

# Set test environment variables
os.environ["ENVIRONMENT"] = "test"
os.environ["DEBUG"] = "false"
os.environ["JWT_SECRET"] = "test-secret-key-for-unit-tests"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["SERVICE_NAME"] = "test-suite"
