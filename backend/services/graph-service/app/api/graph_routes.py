"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Graph Service API routes.
"""

from uuid import UUID

from app.schemas.graph_schema import (
    GraphStatsResponse,
    KnowledgeClustersResponse,
    NeighborResponse,
    NodeResponse,
    RelatedEntitiesResponse,
    SubgraphResponse,
)
from app.services.graph_service import GraphService
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.database.connection import get_db_session

router = APIRouter()


def _get_user_id(x_user_id: str = Header(..., alias="X-User-ID")) -> UUID:
    """Extract user ID from X-User-ID header (injected by API gateway)."""
    return UUID(x_user_id)


def _get_redis(request: Request):
    """Get Redis client from app state."""
    return getattr(request.app.state, "redis", None)


@router.get("/graph/node/{node_id}", response_model=NodeResponse, tags=["Graph"])
async def get_node(
    node_id: UUID,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
    request: Request = None,
):
    """Get a node by ID."""
    svc = GraphService(session, redis_client=_get_redis(request))
    node = await svc.get_node(user_id, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node


@router.get(
    "/graph/neighbors/{node_id}", response_model=NeighborResponse, tags=["Graph"]
)
async def get_neighbors(
    node_id: UUID,
    limit: int = Query(50, ge=1, le=100, description="Max neighbors to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
    request: Request = None,
):
    """Get a node with its direct neighbors (supports pagination via offset/limit)."""
    svc = GraphService(session, redis_client=_get_redis(request))
    response = await svc.get_neighbors(user_id, node_id, limit=limit, offset=offset)
    if not response:
        raise HTTPException(status_code=404, detail="Node not found")
    return response


@router.get("/graph/subgraph", response_model=SubgraphResponse, tags=["Graph"])
async def get_subgraph(
    node_id: UUID = Query(..., description="Root node for subgraph"),
    depth: int = Query(2, ge=1, le=5, description="Max depth for BFS traversal"),
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
    request: Request = None,
):
    """Get a subgraph centered on a node (BFS with configurable depth)."""
    svc = GraphService(session, redis_client=_get_redis(request))
    response = await svc.get_subgraph(user_id, node_id, depth=depth)
    if not response:
        raise HTTPException(status_code=404, detail="Node not found")
    return response


@router.get("/graph/stats", response_model=GraphStatsResponse, tags=["Graph"])
async def get_stats(
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """Get graph statistics for the user."""
    svc = GraphService(session)
    stats = await svc.get_stats(user_id)
    return stats


@router.get(
    "/graph/find-related-notes/{node_id}",
    response_model=RelatedEntitiesResponse,
    tags=["Graph Queries"],
)
async def find_related_notes(
    node_id: UUID,
    depth: int = Query(3, ge=1, le=5, description="Max depth for traversal"),
    limit: int = Query(50, ge=1, le=100, description="Max notes to return"),
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
    request: Request = None,
):
    """Find all notes related to a given node within specified depth."""
    svc = GraphService(session, redis_client=_get_redis(request))
    response = await svc.find_related_notes(user_id, node_id, depth=depth, limit=limit)
    if not response:
        raise HTTPException(status_code=404, detail="Node not found")
    return response


@router.get(
    "/graph/find-connected-habits/{node_id}",
    response_model=RelatedEntitiesResponse,
    tags=["Graph Queries"],
)
async def find_connected_habits(
    node_id: UUID,
    depth: int = Query(3, ge=1, le=5, description="Max depth for traversal"),
    limit: int = Query(50, ge=1, le=100, description="Max habits to return"),
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
    request: Request = None,
):
    """Find all habits connected to a given node within specified depth."""
    svc = GraphService(session, redis_client=_get_redis(request))
    response = await svc.find_connected_habits(
        user_id, node_id, depth=depth, limit=limit
    )
    if not response:
        raise HTTPException(status_code=404, detail="Node not found")
    return response


@router.get(
    "/graph/find-knowledge-clusters",
    response_model=KnowledgeClustersResponse,
    tags=["Graph Queries"],
)
async def find_knowledge_clusters(
    cluster_threshold: int = Query(3, ge=1, le=10, description="Minimum cluster size"),
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
    request: Request = None,
):
    """Find knowledge clusters (dense subgraphs) in the user's graph."""
    svc = GraphService(session, redis_client=_get_redis(request))
    response = await svc.find_knowledge_clusters(
        user_id, cluster_threshold=cluster_threshold
    )
    return response
