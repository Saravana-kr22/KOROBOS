from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx
import logging

# CortexOS API Gateway
# §5 Kubernetes Cluster Setup — API Gateway entry point

app = FastAPI(title="CortexOS API Gateway")
logger = logging.getLogger("api-gateway")

# Service routing map
SERVICES = {
    "auth": "http://localhost:8000",
    "notes": "http://localhost:8001",
    "habits": "http://localhost:8002",
    "learning": "http://localhost:8003",
    "health": "http://localhost:8004",
    "analytics": "http://localhost:8005",
    "notifications": "http://localhost:8006",
    "ai": "http://localhost:8007",
}

@app.api_route("/api/v1/{service_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def gateway(request: Request, service_path: str):
    # Determine target service from the first part of the path
    parts = service_path.split("/")
    if not parts:
        raise HTTPException(status_code=404, detail="Invalid path")
    
    svc_key = parts[0]
    if svc_key not in SERVICES:
        raise HTTPException(status_code=404, detail=f"Service {svc_key} not found")
    
    target_url = SERVICES[svc_key]
    # Reconstruct the path for the downstream service
    remaining_path = "/".join(parts[1:])
    full_url = f"{target_url}/{remaining_path}"
    
    async with httpx.AsyncClient() as client:
        try:
            # Proxy the request
            response = await client.request(
                method=request.method,
                url=full_url,
                headers=dict(request.headers),
                params=dict(request.query_params),
                content=await request.body()
            )
            return JSONResponse(
                content=response.json() if "application/json" in response.headers.get("content-type", "") else response.text,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
        except Exception as e:
            logger.error(f"Error proxying request to {full_url}: {str(e)}")
            raise HTTPException(status_code=502, detail="Bad Gateway")

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "api-gateway"}
