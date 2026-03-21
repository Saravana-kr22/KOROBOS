"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Service Registry for the API Gateway.
Maps service names to their base URLs from configuration.
"""

from typing import Optional

from app.config.gateway_settings import get_gateway_settings


class ServiceRegistry:
    """
    Registry that maps logical service names to their network addresses.

    Service URLs are sourced from environment variables via GatewaySettings,
    allowing Kubernetes DNS or Docker Compose networking to provide addresses.
    """

    def __init__(self):
        settings = get_gateway_settings()
        self._services: dict[str, str] = {
            "auth": settings.services_auth,
            "notes": settings.services_notes,
            "habits": settings.services_habits,
            "learning": settings.services_learning,
            "health": settings.services_health,
            "analytics": settings.services_analytics,
            "notifications": settings.services_notifications,
            "ai": settings.services_ai,
            "database": settings.services_database,
            "dashboard": settings.services_dashboard,
        }

    def get_service_url(self, service_name: str) -> Optional[str]:
        """
        Return the base URL for the given service name.

        Args:
            service_name: Logical service name (e.g. "auth", "notes").

        Returns:
            Base URL string or None if service is not registered.
        """
        return self._services.get(service_name)

    def list_services(self) -> dict[str, str]:
        """Return a copy of the full service name → URL mapping."""
        return dict(self._services)
