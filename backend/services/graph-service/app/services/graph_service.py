"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Business logic for the Graph Service.
"""

from typing import Optional
from uuid import UUID

import redis.asyncio as aioredis
from app.models.graph_model import GraphEdge, GraphNode
from app.repositories.graph_repository import GraphRepository
from app.schemas.graph_schema import (
    EdgeResponse,
    GraphStatsResponse,
    KnowledgeClusterResponse,
    KnowledgeClustersResponse,
    NeighborResponse,
    NodeResponse,
    RelatedEntitiesResponse,
    SubgraphResponse,
)
from sqlalchemy.ext.asyncio import AsyncSession


class GraphService:
    """Business logic for Graph Service with Redis caching."""

    def __init__(
        self, session: AsyncSession, redis_client: Optional[aioredis.Redis] = None
    ):
        self.repo = GraphRepository(session)
        self.redis = redis_client
        self.cache_ttl = 300  # 5 minutes

    async def _get_node_response(self, node: GraphNode) -> NodeResponse:
        """Convert GraphNode model to response schema."""
        return NodeResponse(
            id=node.id,
            user_id=node.user_id,
            type=node.type,
            title=node.title,
            source_id=node.source_id,
            metadata=node.metadata_json,
            created_at=node.created_at,
            updated_at=node.updated_at,
        )

    async def _get_edge_response(self, edge: GraphEdge) -> EdgeResponse:
        """Convert GraphEdge model to response schema."""
        return EdgeResponse(
            id=edge.id,
            user_id=edge.user_id,
            source_node_id=edge.source_node_id,
            target_node_id=edge.target_node_id,
            relation_type=edge.relation_type,
            created_at=edge.created_at,
        )

    async def upsert_node(
        self,
        user_id: UUID,
        type: str,
        title: str,
        source_id: UUID,
        metadata: Optional[dict] = None,
    ) -> NodeResponse:
        """Create or update a node."""
        node = await self.repo.upsert_node(user_id, type, title, source_id, metadata)

        # Invalidate cache
        await self.invalidate_node_cache(node.id)

        return await self._get_node_response(node)

    async def delete_node(self, source_id: UUID) -> None:
        """Delete a node by source_id."""
        # First find the node to get its ID for cache invalidation
        node = await self.repo.find_node_by_source(source_id)
        if node:
            await self.invalidate_node_cache(node.id)

        # Delete the node
        await self.repo.delete_node_by_source(source_id)

    async def create_edge(
        self,
        user_id: UUID,
        source_node_id: UUID,
        target_node_id: UUID,
        relation_type: str,
    ) -> EdgeResponse:
        """Create an edge between two nodes."""
        edge = await self.repo.create_edge(
            user_id, source_node_id, target_node_id, relation_type
        )

        # Invalidate cache for both nodes
        await self.invalidate_node_cache(source_node_id)
        await self.invalidate_node_cache(target_node_id)

        return await self._get_edge_response(edge)

    async def get_node(self, user_id: UUID, node_id: UUID) -> Optional[NodeResponse]:
        """Get a node by ID with caching."""
        # Try cache first
        cache_key = f"graph:node:{node_id}"
        if self.redis:
            try:
                cached = await self.redis.get(cache_key)
                if cached:
                    return NodeResponse.model_validate_json(cached)
            except Exception:
                pass  # Fall through to DB

        # Get from DB
        node = await self.repo.get_node(user_id, node_id)
        if not node:
            return None

        response = await self._get_node_response(node)

        # Cache the result
        if self.redis:
            try:
                await self.redis.setex(
                    cache_key, self.cache_ttl, response.model_dump_json()
                )
            except Exception:
                pass  # Cache failure is not critical

        return response

    async def get_neighbors(
        self, user_id: UUID, node_id: UUID, limit: int = 50, offset: int = 0
    ) -> Optional[NeighborResponse]:
        """Get a node with its direct neighbors (with pagination support)."""
        # For paginated requests, skip caching (cache only first page)
        cache_key = f"graph:neighbors:{node_id}:0" if offset == 0 else None

        if cache_key and self.redis:
            try:
                cached = await self.redis.get(cache_key)
                if cached:
                    return NeighborResponse.model_validate_json(cached)
            except Exception:
                pass

        # Get from DB with offset support
        node, edges, neighbors = await self.repo.get_neighbors(
            user_id, node_id, limit, offset
        )
        if not node:
            return None

        node_response = await self._get_node_response(node)
        edge_responses = [await self._get_edge_response(e) for e in edges]
        neighbor_responses = [await self._get_node_response(n) for n in neighbors]

        response = NeighborResponse(
            node=node_response,
            edges=edge_responses,
            neighbors=neighbor_responses,
        )

        # Cache only first page
        if cache_key and self.redis:
            try:
                await self.redis.setex(
                    cache_key, self.cache_ttl, response.model_dump_json()
                )
            except Exception:
                pass

        return response

    async def get_subgraph(
        self, user_id: UUID, node_id: UUID, depth: int = 2
    ) -> Optional[SubgraphResponse]:
        """Get a subgraph centered on a node."""
        # Try cache first
        cache_key = f"graph:subgraph:{node_id}"
        if self.redis:
            try:
                cached = await self.redis.get(cache_key)
                if cached:
                    return SubgraphResponse.model_validate_json(cached)
            except Exception:
                pass

        # Verify node exists and belongs to user
        node = await self.repo.get_node(user_id, node_id)
        if not node:
            return None

        # Get subgraph from DB
        nodes, edges = await self.repo.get_subgraph(user_id, node_id, depth)

        node_responses = [await self._get_node_response(n) for n in nodes]
        edge_responses = [await self._get_edge_response(e) for e in edges]

        response = SubgraphResponse(nodes=node_responses, edges=edge_responses)

        # Cache the result
        if self.redis:
            try:
                await self.redis.setex(
                    cache_key, self.cache_ttl, response.model_dump_json()
                )
            except Exception:
                pass

        return response

    async def get_stats(self, user_id: UUID) -> GraphStatsResponse:
        """Get graph statistics for a user."""
        (
            total_nodes,
            total_edges,
            node_types,
            relation_types,
        ) = await self.repo.get_stats(user_id)

        return GraphStatsResponse(
            total_nodes=total_nodes,
            total_edges=total_edges,
            node_types=node_types,
            relation_types=relation_types,
        )

    async def invalidate_node_cache(self, node_id: UUID) -> None:
        """Invalidate cache for a node and related queries."""
        if self.redis:
            try:
                await self.redis.delete(f"graph:node:{node_id}")
                await self.redis.delete(f"graph:neighbors:{node_id}")
                await self.redis.delete(f"graph:subgraph:{node_id}")
            except Exception:
                pass  # Cache invalidation failure is not critical

    async def find_related_notes(
        self, user_id: UUID, node_id: UUID, depth: int = 3, limit: int = 50
    ) -> Optional[RelatedEntitiesResponse]:
        """Find all notes related to a given node."""
        # Try cache first
        cache_key = f"graph:related_notes:{node_id}"
        if self.redis:
            try:
                cached = await self.redis.get(cache_key)
                if cached:
                    return RelatedEntitiesResponse.model_validate_json(cached)
            except Exception:
                pass

        # Verify user has access to the node
        node = await self.repo.get_node(user_id, node_id)
        if not node:
            return None

        # Get related notes from DB
        related_nodes = await self.repo.find_related_notes(
            user_id, node_id, depth, limit
        )

        node_responses = [await self._get_node_response(n) for n in related_nodes]

        response = RelatedEntitiesResponse(
            entity_type="note",
            count=len(node_responses),
            nodes=node_responses,
        )

        # Cache the result
        if self.redis:
            try:
                await self.redis.setex(
                    cache_key, self.cache_ttl, response.model_dump_json()
                )
            except Exception:
                pass

        return response

    async def find_connected_habits(
        self, user_id: UUID, node_id: UUID, depth: int = 3, limit: int = 50
    ) -> Optional[RelatedEntitiesResponse]:
        """Find all habits connected to a given node."""
        # Try cache first
        cache_key = f"graph:connected_habits:{node_id}"
        if self.redis:
            try:
                cached = await self.redis.get(cache_key)
                if cached:
                    return RelatedEntitiesResponse.model_validate_json(cached)
            except Exception:
                pass

        # Verify user has access to the node
        node = await self.repo.get_node(user_id, node_id)
        if not node:
            return None

        # Get connected habits from DB
        habit_nodes = await self.repo.find_connected_habits(
            user_id, node_id, depth, limit
        )

        node_responses = [await self._get_node_response(n) for n in habit_nodes]

        response = RelatedEntitiesResponse(
            entity_type="habit",
            count=len(node_responses),
            nodes=node_responses,
        )

        # Cache the result
        if self.redis:
            try:
                await self.redis.setex(
                    cache_key, self.cache_ttl, response.model_dump_json()
                )
            except Exception:
                pass

        return response

    async def find_knowledge_clusters(
        self, user_id: UUID, cluster_threshold: int = 3
    ) -> KnowledgeClustersResponse:
        """Find knowledge clusters (dense subgraphs) in the user's graph."""
        # Try cache first
        cache_key = f"graph:clusters:{user_id}"
        if self.redis:
            try:
                cached = await self.redis.get(cache_key)
                if cached:
                    return KnowledgeClustersResponse.model_validate_json(cached)
            except Exception:
                pass

        # Get clusters from repository
        cluster_data = await self.repo.find_knowledge_clusters(
            user_id, cluster_threshold
        )

        # Fetch node details for each cluster
        cluster_responses = []
        for idx, cluster in enumerate(cluster_data):
            node_ids = cluster["node_ids"]

            # Get full node objects
            nodes_result = await self.repo.session.execute(
                __import__("sqlalchemy")
                .select(GraphNode)
                .where(GraphNode.id.in_(node_ids))
            )
            nodes = list(nodes_result.scalars().all())

            node_responses = [await self._get_node_response(n) for n in nodes]

            cluster_response = KnowledgeClusterResponse(
                cluster_id=idx,
                size=cluster["size"],
                node_ids=node_ids,
                nodes=node_responses,
            )
            cluster_responses.append(cluster_response)

        response = KnowledgeClustersResponse(
            total_clusters=len(cluster_responses),
            clusters=cluster_responses,
        )

        # Cache the result (longer TTL for clusters as they change less frequently)
        if self.redis:
            try:
                await self.redis.setex(
                    cache_key, self.cache_ttl * 2, response.model_dump_json()
                )
            except Exception:
                pass

        return response
