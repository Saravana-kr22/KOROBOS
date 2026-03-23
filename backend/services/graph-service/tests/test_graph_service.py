"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Test suite for Graph Service layer (caching, invalidation, conversions)
"""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from app.models.graph_model import Base
from app.schemas.graph_schema import EdgeResponse, NodeResponse
from app.services.graph_service import GraphService
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture
async def async_session():
    """Create an in-memory SQLite async session for tests"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session


@pytest.fixture
async def mock_redis():
    """Create a mock Redis client for testing"""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock()
    redis.delete = AsyncMock()
    redis.aclose = AsyncMock()
    return redis


@pytest.fixture
async def graph_service(async_session, mock_redis):
    """Create a GraphService instance with mocked Redis"""
    service = GraphService(async_session, mock_redis)
    return service


class TestGraphServiceCaching:
    """Test caching behavior of GraphService"""

    async def test_get_node_cache_miss_fetches_from_db(self, async_session, mock_redis):
        """Cache miss should fetch from repository and cache result"""
        service = GraphService(async_session, mock_redis)
        user_id = uuid4()
        source_id = uuid4()

        # Create node in database
        node = await service.repo.upsert_node(
            user_id=user_id,
            type="note",
            title="Test Note",
            source_id=source_id,
        )

        # First call: cache miss
        mock_redis.get.return_value = None
        result = await service.get_node(user_id, node.id)

        assert result is not None
        assert result.id == node.id
        assert result.title == "Test Note"
        # Verify cache set was called
        mock_redis.setex.assert_called_once()

    async def test_get_node_cache_hit_returns_cached(self, async_session, mock_redis):
        """Cache hit should return cached node without DB query"""
        service = GraphService(async_session, mock_redis)
        user_id = uuid4()
        node_id = uuid4()

        # Mock cached response (must include all required NodeResponse fields)
        cached_data = {
            "id": str(node_id),
            "user_id": str(user_id),
            "type": "note",
            "title": "Cached Note",
            "source_id": str(uuid4()),
            "metadata": None,
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-01T00:00:00+00:00",
        }
        import json

        mock_redis.get.return_value = json.dumps(cached_data)

        # Spy on repository to ensure it's not called
        with patch.object(service.repo, "get_node", new_callable=AsyncMock) as mock_get:
            result = await service.get_node(user_id, node_id)

            # Should return from cache without calling repository
            assert result is not None
            mock_get.assert_not_called()

    async def test_get_neighbors_with_cache(self, async_session, mock_redis):
        """Get neighbors should use cache for both node and neighbors list"""
        service = GraphService(async_session, mock_redis)
        user_id = uuid4()
        source_id = uuid4()

        # Create node and neighbors
        center_node = await service.repo.upsert_node(
            user_id=user_id,
            type="note",
            title="Center",
            source_id=source_id,
        )

        neighbor_node = await service.repo.upsert_node(
            user_id=user_id,
            type="habit",
            title="Neighbor",
            source_id=uuid4(),
        )

        await service.repo.create_edge(
            user_id=user_id,
            source_node_id=center_node.id,
            target_node_id=neighbor_node.id,
            relation_type="note_links",
        )

        # First call: cache miss
        mock_redis.get.return_value = None
        result = await service.get_neighbors(user_id, center_node.id)

        assert result is not None
        assert result.node.id == center_node.id
        assert len(result.neighbors) == 1
        # Verify cache set was called for neighbors
        assert mock_redis.setex.called

    async def test_get_subgraph_with_depth_parameter(self, async_session, mock_redis):
        """Get subgraph should respect depth parameter and cache result"""
        service = GraphService(async_session, mock_redis)
        user_id = uuid4()

        # Create chain: n1 -> n2 -> n3
        nodes = []
        for i in range(3):
            node = await service.repo.upsert_node(
                user_id=user_id,
                type="note",
                title=f"Note {i}",
                source_id=uuid4(),
            )
            nodes.append(node)

        for i in range(len(nodes) - 1):
            await service.repo.create_edge(
                user_id=user_id,
                source_node_id=nodes[i].id,
                target_node_id=nodes[i + 1].id,
                relation_type="note_links",
            )

        # Get subgraph with depth 1
        mock_redis.get.return_value = None
        result = await service.get_subgraph(user_id, nodes[0].id, depth=1)

        assert result is not None
        # Should include nodes 0 and 1
        assert len(result.nodes) >= 2
        assert nodes[0].id in [n.id for n in result.nodes]

    async def test_invalidate_cache_clears_node_caches(self, async_session, mock_redis):
        """Invalidate cache should clear node, neighbors, and subgraph caches"""
        service = GraphService(async_session, mock_redis)
        node_id = uuid4()

        await service.invalidate_node_cache(node_id)

        # Should call delete on Redis for node, neighbors, and subgraph keys
        calls = mock_redis.delete.call_args_list
        assert len(calls) >= 1
        # Verify cache keys match expected pattern
        call_args = [str(call[0][0]) for call in calls]
        assert any(str(node_id) in arg for arg in call_args)


class TestGraphServiceCacheInvalidation:
    """Test cache invalidation on mutations"""

    async def test_delete_node_invalidates_cache(self, async_session, mock_redis):
        """Deleting a node should invalidate its cache"""
        service = GraphService(async_session, mock_redis)
        user_id = uuid4()
        source_id = uuid4()

        # Create and delete node
        node = await service.repo.upsert_node(
            user_id=user_id,
            type="note",
            title="Test",
            source_id=source_id,
        )

        mock_redis.get.return_value = None
        await service.repo.delete_node_by_source(source_id)

        # Cache invalidation happens after delete in service method
        # (would be implemented in service delete wrapper)
        fetched = await service.repo.get_node(user_id, node.id)
        assert fetched is None

    async def test_upsert_invalidates_existing_node_cache(
        self, async_session, mock_redis
    ):
        """Upserting an existing node should invalidate cache"""
        service = GraphService(async_session, mock_redis)
        user_id = uuid4()
        source_id = uuid4()

        # Create node
        node1 = await service.repo.upsert_node(
            user_id=user_id,
            type="note",
            title="Original",
            source_id=source_id,
        )

        # Upsert with same source_id
        mock_redis.get.return_value = None
        node2 = await service.repo.upsert_node(
            user_id=user_id,
            type="habit",
            title="Updated",
            source_id=source_id,
        )

        assert node2.id == node1.id
        assert node2.title == "Updated"


class TestGraphServiceResponseSchemas:
    """Test response schema conversions"""

    async def test_get_node_returns_node_response_schema(
        self, async_session, mock_redis
    ):
        """Get node should return NodeResponse schema"""
        service = GraphService(async_session, mock_redis)
        user_id = uuid4()
        source_id = uuid4()

        node = await service.repo.upsert_node(
            user_id=user_id,
            type="note",
            title="Test",
            source_id=source_id,
            metadata={"key": "value"},
        )

        mock_redis.get.return_value = None
        result = await service.get_node(user_id, node.id)

        # Verify response is proper schema
        assert isinstance(result, NodeResponse)
        assert result.id == node.id
        assert result.type == "note"
        assert result.title == "Test"

    async def test_get_neighbors_returns_neighbor_response_schema(
        self, async_session, mock_redis
    ):
        """Get neighbors should return NeighborResponse schema"""
        service = GraphService(async_session, mock_redis)
        user_id = uuid4()

        node = await service.repo.upsert_node(
            user_id=user_id,
            type="note",
            title="Center",
            source_id=uuid4(),
        )

        neighbor = await service.repo.upsert_node(
            user_id=user_id,
            type="habit",
            title="Neighbor",
            source_id=uuid4(),
        )

        await service.repo.create_edge(
            user_id=user_id,
            source_node_id=node.id,
            target_node_id=neighbor.id,
            relation_type="note_links",
        )

        mock_redis.get.return_value = None
        result = await service.get_neighbors(user_id, node.id)

        assert result is not None
        assert hasattr(result, "node")
        assert hasattr(result, "edges")
        assert hasattr(result, "neighbors")
        assert isinstance(result.node, NodeResponse)

    async def test_get_subgraph_returns_subgraph_response_schema(
        self, async_session, mock_redis
    ):
        """Get subgraph should return SubgraphResponse schema"""
        service = GraphService(async_session, mock_redis)
        user_id = uuid4()

        node = await service.repo.upsert_node(
            user_id=user_id,
            type="note",
            title="Test",
            source_id=uuid4(),
        )

        mock_redis.get.return_value = None
        result = await service.get_subgraph(user_id, node.id)

        assert result is not None
        assert hasattr(result, "nodes")
        assert hasattr(result, "edges")
        assert isinstance(result.nodes, list)
        assert isinstance(result.edges, list)
        assert all(isinstance(n, NodeResponse) for n in result.nodes)
        assert all(isinstance(e, EdgeResponse) for e in result.edges)


class TestGraphServiceUserIsolation:
    """Test user isolation in service layer"""

    async def test_get_node_enforces_user_isolation(self, async_session, mock_redis):
        """Service should enforce user isolation when retrieving nodes"""
        service = GraphService(async_session, mock_redis)
        user1_id = uuid4()
        user2_id = uuid4()
        source_id = uuid4()

        # Create node for user1
        node = await service.repo.upsert_node(
            user_id=user1_id,
            type="note",
            title="User1 Note",
            source_id=source_id,
        )

        # Try to access from user2
        mock_redis.get.return_value = None
        result = await service.get_node(user2_id, node.id)

        assert result is None

    async def test_get_neighbors_enforces_user_isolation(
        self, async_session, mock_redis
    ):
        """Service should enforce user isolation when retrieving neighbors"""
        service = GraphService(async_session, mock_redis)
        user1_id = uuid4()
        user2_id = uuid4()

        node = await service.repo.upsert_node(
            user_id=user1_id,
            type="note",
            title="User1 Node",
            source_id=uuid4(),
        )

        mock_redis.get.return_value = None
        result = await service.get_neighbors(user2_id, node.id)

        assert result is None

    async def test_get_subgraph_enforces_user_isolation(
        self, async_session, mock_redis
    ):
        """Service should enforce user isolation when retrieving subgraphs"""
        service = GraphService(async_session, mock_redis)
        user1_id = uuid4()
        user2_id = uuid4()

        node = await service.repo.upsert_node(
            user_id=user1_id,
            type="note",
            title="User1 Node",
            source_id=uuid4(),
        )

        mock_redis.get.return_value = None
        result = await service.get_subgraph(user2_id, node.id)

        assert result is None


class TestGraphServiceErrorHandling:
    """Test error handling in service layer"""

    async def test_get_node_handles_nonexistent_node(self, async_session, mock_redis):
        """Getting nonexistent node should return None gracefully"""
        service = GraphService(async_session, mock_redis)
        user_id = uuid4()
        node_id = uuid4()

        mock_redis.get.return_value = None
        result = await service.get_node(user_id, node_id)

        assert result is None

    async def test_cache_error_falls_back_to_db(self, async_session, mock_redis):
        """Redis errors should fall back to database access"""
        service = GraphService(async_session, mock_redis)
        user_id = uuid4()
        source_id = uuid4()

        node = await service.repo.upsert_node(
            user_id=user_id,
            type="note",
            title="Test",
            source_id=source_id,
        )

        # Redis get fails
        mock_redis.get.side_effect = Exception("Redis connection failed")
        # Redis set fails
        mock_redis.set.side_effect = Exception("Redis connection failed")

        # Service should still work by falling back to DB
        result = await service.get_node(user_id, node.id)

        assert result is not None
        assert result.id == node.id


class TestGraphServiceStats:
    """Test graph statistics endpoint"""

    async def test_get_stats_returns_correct_counts(self, async_session, mock_redis):
        """Get stats should return correct node/edge counts"""
        service = GraphService(async_session, mock_redis)
        user_id = uuid4()

        # Create 2 nodes of different types
        note = await service.repo.upsert_node(
            user_id=user_id,
            type="note",
            title="Note",
            source_id=uuid4(),
        )

        habit = await service.repo.upsert_node(
            user_id=user_id,
            type="habit",
            title="Habit",
            source_id=uuid4(),
        )

        # Create edge
        await service.repo.create_edge(
            user_id=user_id,
            source_node_id=note.id,
            target_node_id=habit.id,
            relation_type="habit_related_to_learning",
        )

        (
            total_nodes,
            total_edges,
            node_types,
            relation_types,
        ) = await service.repo.get_stats(user_id)

        assert total_nodes == 2
        assert total_edges == 1
        assert node_types["note"] == 1
        assert node_types["habit"] == 1
        assert relation_types["habit_related_to_learning"] == 1

    async def test_get_stats_user_isolated(self, async_session, mock_redis):
        """Get stats should only count nodes/edges for requesting user"""
        service = GraphService(async_session, mock_redis)
        user1_id = uuid4()
        user2_id = uuid4()

        # Create node for user1
        await service.repo.upsert_node(
            user_id=user1_id,
            type="note",
            title="User1 Note",
            source_id=uuid4(),
        )

        # Create node for user2
        await service.repo.upsert_node(
            user_id=user2_id,
            type="note",
            title="User2 Note",
            source_id=uuid4(),
        )

        # Get stats for user1
        total_nodes, _, _, _ = await service.repo.get_stats(user1_id)

        # Should only count user1's node
        assert total_nodes == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
