"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Data access layer for the Graph Service.
"""

from typing import Optional
from uuid import UUID

from app.models.graph_model import GraphEdge, GraphNode
from sqlalchemy import and_, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession


class GraphRepository:
    """Repository for Graph CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert_node(
        self,
        user_id: UUID,
        type: str,
        title: str,
        source_id: UUID,
        metadata: Optional[dict] = None,
    ) -> GraphNode:
        """Upsert a node by source_id (creates if not exists, updates if exists)."""
        # Try to find existing node by source_id
        result = await self.session.execute(
            select(GraphNode).where(
                and_(GraphNode.user_id == user_id, GraphNode.source_id == source_id)
            )
        )
        node = result.scalar_one_or_none()

        if node:
            # Update existing node
            node.type = type
            node.title = title
            if metadata:
                node.metadata_json = metadata
        else:
            # Create new node
            node = GraphNode(
                user_id=user_id,
                type=type,
                title=title,
                source_id=source_id,
                metadata_json=metadata,
            )
            self.session.add(node)

        await self.session.flush()
        return node

    async def delete_node_by_source(self, source_id: UUID) -> None:
        """Delete node by source_id (cascade deletes edges)."""
        result = await self.session.execute(
            select(GraphNode).where(GraphNode.source_id == source_id)
        )
        node = result.scalar_one_or_none()
        if node:
            await self.session.delete(node)
            await self.session.flush()

    async def find_node_by_source(self, source_id: UUID) -> Optional[GraphNode]:
        """Find node by source_id."""
        result = await self.session.execute(
            select(GraphNode).where(GraphNode.source_id == source_id)
        )
        return result.scalar_one_or_none()

    async def get_node(self, user_id: UUID, node_id: UUID) -> Optional[GraphNode]:
        """Get node by ID, ensuring user isolation."""
        result = await self.session.execute(
            select(GraphNode).where(
                and_(GraphNode.id == node_id, GraphNode.user_id == user_id)
            )
        )
        return result.scalar_one_or_none()

    async def create_edge(
        self,
        user_id: UUID,
        source_node_id: UUID,
        target_node_id: UUID,
        relation_type: str,
    ) -> GraphEdge:
        """Create an edge between two nodes."""
        edge = GraphEdge(
            user_id=user_id,
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            relation_type=relation_type,
        )
        self.session.add(edge)
        await self.session.flush()
        return edge

    async def get_neighbors(
        self, user_id: UUID, node_id: UUID, limit: int = 50, offset: int = 0
    ) -> tuple[GraphNode, list[GraphEdge], list[GraphNode]]:
        """Get node with direct neighbors (one-hop) with pagination."""
        # Get the node
        node_result = await self.session.execute(
            select(GraphNode).where(
                and_(GraphNode.id == node_id, GraphNode.user_id == user_id)
            )
        )
        node = node_result.scalar_one_or_none()
        if not node:
            return None, [], []

        # Get outgoing edges with offset/limit (proper SQL pagination)
        edges_result = await self.session.execute(
            select(GraphEdge)
            .where(
                and_(
                    GraphEdge.source_node_id == node_id,
                    GraphEdge.user_id == user_id,
                )
            )
            .offset(offset)
            .limit(limit)
        )
        edges = list(edges_result.scalars().all())

        # Get target nodes
        if edges:
            target_ids = [edge.target_node_id for edge in edges]
            nodes_result = await self.session.execute(
                select(GraphNode).where(GraphNode.id.in_(target_ids))
            )
            neighbors = list(nodes_result.scalars().all())
        else:
            neighbors = []

        return node, edges, neighbors

    async def get_subgraph(
        self, user_id: UUID, node_id: UUID, depth: int = 2
    ) -> tuple[list[GraphNode], list[GraphEdge]]:
        """Get subgraph using Python-level BFS (portable across all databases)."""
        visited: set[UUID] = set()
        current_level: set[UUID] = {node_id}
        all_nodes: list[GraphNode] = []
        all_edges: list[GraphEdge] = []

        for level in range(depth + 1):
            if not current_level:
                break

            # Fetch nodes in current level that belong to user
            nodes_result = await self.session.execute(
                select(GraphNode).where(
                    and_(
                        GraphNode.id.in_(current_level),
                        GraphNode.user_id == user_id,
                    )
                )
            )
            nodes = list(nodes_result.scalars().all())
            if not nodes:
                break
            all_nodes.extend(nodes)
            visited.update(current_level)

            if level < depth:
                # Get outgoing edges from current level nodes
                edges_result = await self.session.execute(
                    select(GraphEdge).where(
                        and_(
                            GraphEdge.source_node_id.in_(current_level),
                            GraphEdge.user_id == user_id,
                        )
                    )
                )
                edges = list(edges_result.scalars().all())
                all_edges.extend(edges)

                # Next level: target nodes not yet visited
                current_level = {e.target_node_id for e in edges} - visited

        return all_nodes, all_edges

    async def get_stats(self, user_id: UUID) -> tuple[int, int, dict, dict]:
        """Get graph statistics for a user."""
        # Total nodes
        nodes_count = (
            await self.session.execute(
                select(func.count())
                .select_from(GraphNode)
                .where(GraphNode.user_id == user_id)
            )
        ).scalar_one()

        # Total edges
        edges_count = (
            await self.session.execute(
                select(func.count())
                .select_from(GraphEdge)
                .where(GraphEdge.user_id == user_id)
            )
        ).scalar_one()

        # Nodes per type
        types_result = await self.session.execute(
            select(GraphNode.type, func.count(GraphNode.id))
            .where(GraphNode.user_id == user_id)
            .group_by(GraphNode.type)
        )
        node_types = {row[0]: row[1] for row in types_result.all()}

        # Edges per relation type
        relations_result = await self.session.execute(
            select(GraphEdge.relation_type, func.count(GraphEdge.id))
            .where(GraphEdge.user_id == user_id)
            .group_by(GraphEdge.relation_type)
        )
        relation_types = {row[0]: row[1] for row in relations_result.all()}

        return nodes_count, edges_count, node_types, relation_types

    async def find_related_notes(
        self, user_id: UUID, node_id: UUID, depth: int = 3, limit: int = 50
    ) -> list[GraphNode]:
        """Find all notes connected to a given node up to specified depth."""
        # Use recursive CTE to find connected notes
        query = text(
            """
        WITH RECURSIVE graph_traversal AS (
            -- Base case: start node
            SELECT id, 1 as level
            FROM graph_nodes
            WHERE id = :node_id AND user_id = :user_id

            UNION ALL

            -- Recursive case: follow edges
            SELECT DISTINCT gn.id, gt.level + 1
            FROM graph_traversal gt
            JOIN graph_edges ge ON gt.id = ge.source_node_id
            JOIN graph_nodes gn ON ge.target_node_id = gn.id
            WHERE gt.level < :depth AND gn.user_id = :user_id
        )
        SELECT DISTINCT gn.id, gn.title, gn.type
        FROM graph_traversal gt
        JOIN graph_nodes gn ON gt.id = gn.id
        WHERE gn.type = 'note' AND gn.id != :node_id
        LIMIT :limit
        """
        )

        result = await self.session.execute(
            query,
            {"node_id": node_id, "user_id": user_id, "depth": depth, "limit": limit},
        )
        note_ids = [row[0] for row in result.all()]

        if not note_ids:
            return []

        # Fetch full note objects
        notes_result = await self.session.execute(
            select(GraphNode).where(GraphNode.id.in_(note_ids))
        )
        return list(notes_result.scalars().all())

    async def find_connected_habits(
        self, user_id: UUID, node_id: UUID, depth: int = 3, limit: int = 50
    ) -> list[GraphNode]:
        """Find all habits connected to a given node up to specified depth."""
        # Use recursive CTE to find connected habits
        query = text(
            """
        WITH RECURSIVE graph_traversal AS (
            -- Base case: start node
            SELECT id, 1 as level
            FROM graph_nodes
            WHERE id = :node_id AND user_id = :user_id

            UNION ALL

            -- Recursive case: follow edges
            SELECT DISTINCT gn.id, gt.level + 1
            FROM graph_traversal gt
            JOIN graph_edges ge ON gt.id = ge.source_node_id
            JOIN graph_nodes gn ON ge.target_node_id = gn.id
            WHERE gt.level < :depth AND gn.user_id = :user_id
        )
        SELECT DISTINCT gn.id, gn.title, gn.type
        FROM graph_traversal gt
        JOIN graph_nodes gn ON gt.id = gn.id
        WHERE gn.type = 'habit' AND gn.id != :node_id
        LIMIT :limit
        """
        )

        result = await self.session.execute(
            query,
            {"node_id": node_id, "user_id": user_id, "depth": depth, "limit": limit},
        )
        habit_ids = [row[0] for row in result.all()]

        if not habit_ids:
            return []

        # Fetch full habit objects
        habits_result = await self.session.execute(
            select(GraphNode).where(GraphNode.id.in_(habit_ids))
        )
        return list(habits_result.scalars().all())

    async def find_knowledge_clusters(
        self, user_id: UUID, cluster_threshold: int = 3
    ) -> list[dict]:
        """
        Find knowledge clusters (groups of densely connected nodes).
        Returns list of clusters, each containing node IDs and sizes.
        Clusters are identified by finding sets of nodes with high edge density.
        """
        # Find all nodes and edges for this user
        nodes_result = await self.session.execute(
            select(GraphNode).where(GraphNode.user_id == user_id)
        )
        nodes = list(nodes_result.scalars().all())

        edges_result = await self.session.execute(
            select(GraphEdge).where(GraphEdge.user_id == user_id)
        )
        edges = list(edges_result.scalars().all())

        if not nodes:
            return []

        # Build adjacency map
        adjacency = {node.id: [] for node in nodes}
        for edge in edges:
            adjacency[edge.source_node_id].append(edge.target_node_id)

        # Simple clustering: find connected components and dense subgraphs
        visited = set()
        clusters = []

        for node in nodes:
            if node.id in visited:
                continue

            # BFS to find connected component
            cluster = []
            queue = [node.id]
            cluster_visited = set()

            while queue:
                current = queue.pop(0)
                if current in cluster_visited:
                    continue

                cluster_visited.add(current)
                cluster.append(current)
                visited.add(current)

                # Add neighbors to queue
                for neighbor in adjacency.get(current, []):
                    if neighbor not in cluster_visited:
                        queue.append(neighbor)

            # Only include clusters above threshold size
            if len(cluster) >= cluster_threshold:
                clusters.append(
                    {
                        "size": len(cluster),
                        "node_ids": cluster,
                    }
                )

        return sorted(clusters, key=lambda c: c["size"], reverse=True)
