"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Centralized router that aggregates all dedicated route modules
and provides a generic catch-all proxy for remaining services.
"""

import logging

import httpx
from app.routes.analytics_routes import router as analytics_router
from app.routes.auth_routes import router as auth_router
from app.routes.dashboard_routes import router as dashboard_router
from app.routes.database_routes import databases_router, records_router
from app.routes.habit_routes import router as habit_router
from app.routes.health_routes import router as health_router
from app.routes.learning_routes import router as learning_router
from app.routes.notes_routes import router as notes_router
from app.services.service_registry import ServiceRegistry
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("api-gateway.router")

# Master router
api_router = APIRouter()

# Include dedicated service routers
api_router.include_router(auth_router)
api_router.include_router(notes_router)
api_router.include_router(habit_router)
api_router.include_router(learning_router)
api_router.include_router(health_router)
api_router.include_router(analytics_router)
api_router.include_router(dashboard_router)
api_router.include_router(databases_router)
api_router.include_router(records_router)


# -- Generic catch-all proxy for remaining services --


@api_router.api_route(
    "/api/v1/{service_name}/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    tags=["Gateway Proxy"],
    operation_id="generic_proxy",
)
async def generic_proxy(request: Request, service_name: str, path: str):
    """
    Catch-all proxy for services without dedicated route modules.

    Handles: notifications, ai
    """
    registry = ServiceRegistry()
    target_base = registry.get_service_url(service_name)

    if not target_base:
        return JSONResponse(
            status_code=404,
            content={
                "status": "error",
                "error": {
                    "code": "SERVICE_NOT_FOUND",
                    "message": f"Service '{service_name}' is not registered",
                },
            },
        )

    target_url = f"{target_base}/{path}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            headers = dict(request.headers)
            headers.pop("host", None)

            # Inject user context if authenticated
            user_id = getattr(request.state, "user_id", None)
            if user_id:
                headers["X-User-ID"] = str(user_id)
                headers["X-User-Roles"] = ",".join(
                    getattr(request.state, "roles", ["user"])
                )

            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                params=dict(request.query_params),
                content=await request.body(),
            )

            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type:
                return JSONResponse(
                    content=response.json(),
                    status_code=response.status_code,
                )
            else:
                return JSONResponse(
                    content={"status": "success", "data": response.text},
                    status_code=response.status_code,
                )

        except httpx.ConnectError:
            logger.error(f"Cannot connect to {service_name} at {target_url}")
            return JSONResponse(
                status_code=502,
                content={
                    "status": "error",
                    "error": {
                        "code": "BAD_GATEWAY",
                        "message": f"Cannot connect to {service_name} service",
                    },
                },
            )
        except Exception as exc:
            logger.error(f"Proxy error for {service_name}: {exc}")
            return JSONResponse(
                status_code=502,
                content={
                    "status": "error",
                    "error": {
                        "code": "BAD_GATEWAY",
                        "message": "Error communicating with upstream service",
                    },
                },
            )
