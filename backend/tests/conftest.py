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

# Add service paths for tests that import from service modules
LEARNING_SERVICE_APP = os.path.join(BACKEND_ROOT, "services", "learning-service")
ANALYTICS_SERVICE_APP = os.path.join(BACKEND_ROOT, "services", "analytics-service")

# Add base paths - ORDER MATTERS: PROJECT_ROOT first so "backend" imports work
# then BACKEND_ROOT for shared imports. Service-specific "app" imports
# are handled within the individual test modules where possible,
# but we add them here at lower priority for overall collection.
for path in [
    LEARNING_SERVICE_APP,
    ANALYTICS_SERVICE_APP,
    GATEWAY_APP,
    PROJECT_ROOT,
    BACKEND_ROOT,
]:
    if path and path not in sys.path:
        sys.path.insert(0, path)

# Verify paths are set up correctly
_backend_found = any(
    "backend/__init__.py" in p or "/backend" in p for p in sys.path[:10] if p
)
if not _backend_found:
    # Make sure PROJECT_ROOT is in sys.path so "backend" can be imported
    if PROJECT_ROOT not in sys.path:
        sys.path.insert(0, PROJECT_ROOT)

# Set test environment variables
os.environ["ENVIRONMENT"] = "test"
os.environ["DEBUG"] = "false"
os.environ["JWT_SECRET"] = "test-secret-key-for-unit-tests"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["SERVICE_NAME"] = "test-suite"


def pytest_configure(config):
    """Initialize pytest configuration."""
    pass


def pytest_collection_modifyitems(items):
    """Reorder test items to avoid module namespace collisions.

    Run all tests from one service before moving to another service,
    or use per-test module isolation.

    Uses filename matching (not absolute paths) so ordering works in
    both local and CI environments.
    """
    import os

    learning_tests = []
    learning_integration_tests = []
    analytics_tests = []
    other_tests = []

    for item in items:
        basename = os.path.basename(item.fspath.strpath)
        if basename == "test_learning_service.py":
            learning_tests.append(item)
        elif basename == "test_learning_service_integration.py":
            learning_integration_tests.append(item)
        elif basename == "test_analytics_integration.py":
            analytics_tests.append(item)
        else:
            other_tests.append(item)

    # Reorder: learning service tests first, then other tests, then analytics
    items[:] = (
        learning_tests + learning_integration_tests + other_tests + analytics_tests
    )
