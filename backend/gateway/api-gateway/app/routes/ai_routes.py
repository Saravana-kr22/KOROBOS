"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

AI Service route proxy — forwards /api/v1/ai/* to the ai-service.
"""

import logging

import httpx
from app.services.service_registry import ServiceRegistry
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/v1/ai", tags=["AI"])
logger = logging.getLogger("api-gateway.routes.ai")


@router.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    operation_id="proxy_ai",
)
async def proxy_ai(request: Request, path: str):
    """Forward all /api/v1/ai/* requests to the ai-service."""
    registry = ServiceRegistry()
    target_base = registry.get_service_url("ai")

    if not target_base:
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "error": {
                    "code": "SERVICE_UNAVAILABLE",
                    "message": "AI service not configured",
                },
            },
        )

    target_url = f"{target_base}/{path}"
    return await _proxy_request(request, target_url)


async def _proxy_request(request: Request, target_url: str) -> JSONResponse:
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
                        "message": f"AI service unavailable at {target_url}",
                    },
                },
            )
        except Exception as e:
            logger.error("Error proxying to AI service: %s", e, exc_info=True)
            return JSONResponse(
                status_code=502,
                content={
                    "status": "error",
                    "error": {
                        "code": "BAD_GATEWAY",
                        "message": "Error forwarding request to AI service",
                    },
                },
            )
