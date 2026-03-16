"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Database routes proxy — forwards /api/v1/databases/* and /api/v1/records/*
to the database-service.
"""

import logging

import httpx
from app.services.service_registry import ServiceRegistry
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

databases_router = APIRouter(prefix="/api/v1/databases", tags=["Databases"])
records_router = APIRouter(prefix="/api/v1/records", tags=["Records"])

logger = logging.getLogger("api-gateway.routes.database")


@databases_router.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    operation_id="proxy_databases",
)
async def proxy_databases(request: Request, path: str):
    """Forward all /api/v1/databases/* requests to the database-service."""
    registry = ServiceRegistry()
    target_base = registry.get_service_url("database")

    if not target_base:
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "error": {
                    "code": "SERVICE_UNAVAILABLE",
                    "message": "Database service not configured",
                },
            },
        )

    target_url = f"{target_base}/{path}"
    return await _proxy_request(request, target_url)


@records_router.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    operation_id="proxy_records",
)
async def proxy_records(request: Request, path: str):
    """Forward all /api/v1/records/* requests to the database-service."""
    registry = ServiceRegistry()
    target_base = registry.get_service_url("database")

    if not target_base:
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "error": {
                    "code": "SERVICE_UNAVAILABLE",
                    "message": "Database service not configured",
                },
            },
        )

    target_url = f"{target_base}/{path}"
    return await _proxy_request(request, target_url)


async def _proxy_request(request: Request, target_url: str) -> JSONResponse:
    """Generic HTTP proxy helper.

    Injects user ID and roles from request state into X-User-ID and
    X-User-Roles headers for the upstream service.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            headers = dict(request.headers)
            headers.pop("host", None)

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
            logger.error("Cannot connect to upstream: %s", target_url)
            return JSONResponse(
                status_code=502,
                content={
                    "status": "error",
                    "error": {
                        "code": "BAD_GATEWAY",
                        "message": "Upstream service unavailable",
                    },
                },
            )
        except Exception as exc:
            logger.error("Proxy error: %s", exc)
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
