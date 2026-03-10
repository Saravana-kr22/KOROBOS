"""
CortexOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Helpers for worker processes that need access to a service-local `app` package.
"""

import sys
from pathlib import Path


def configure_service_app_path(service_dir_name: str) -> Path:
    """
    Add a service directory to `sys.path` so workers can import its `app` package.

    Workers are executed as standalone processes, so isolating the service path per
    worker is sufficient even though multiple services use the top-level module name
    `app`.
    """

    backend_root = Path(__file__).resolve().parents[1]
    service_root = backend_root / "services" / service_dir_name
    if not service_root.exists():
        raise FileNotFoundError(f"Service directory not found: {service_root}")

    service_root_str = str(service_root)
    if service_root_str not in sys.path:
        sys.path.insert(0, service_root_str)

    return service_root
