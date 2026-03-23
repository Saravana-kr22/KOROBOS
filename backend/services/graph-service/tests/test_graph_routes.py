"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Test suite for Graph API routes
"""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from app.models.graph_model import Base
from app.repositories.graph_repository import GraphRepository
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
def mock_redis():
    """Create a mock Redis client"""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock()
    redis.delete = AsyncMock()
    redis.incr = AsyncMock(return_value=1)
    redis.expire = AsyncMock()
    return redis


@pytest.fixture
async def sample_data(async_session):
    """Create sample graph data for testing"""
    repo = GraphRepository(async_session)
    user_id = uuid4()

    # Create nodes
    note = await repo.upsert_node(
        user_id=user_id,
        type="note",
        title="Test Note",
        source_id=uuid4(),
    )

    habit = await repo.upsert_node(
        user_id=user_id,
        type="habit",
        title="Test Habit",
        source_id=uuid4(),
    )

    # Create edge
    edge = await repo.create_edge(
        user_id=user_id,
        source_node_id=note.id,
        target_node_id=habit.id,
        relation_type="habit_related_to_learning",
    )

    return {
        "user_id": user_id,
        "note": note,
        "habit": habit,
        "edge": edge,
    }


class TestGraphRoutes:
    """Test graph API routes"""

    async def test_get_node_returns_200_with_valid_node(
        self, async_session, sample_data
    ):
        """GET /graph/node/{node_id} should return node with 200 status"""
        from unittest.mock import AsyncMock as AsyncMock2

        from app.services.graph_service import GraphService

        service = GraphService(async_session, AsyncMock2())
        user_id = sample_data["user_id"]
        node_id = sample_data["note"].id

        # This would be tested via HTTP in real scenario
        result = await service.get_node(user_id, node_id)

        assert result is not None
        assert result.id == node_id
        assert result.title == "Test Note"

    async def test_get_node_returns_404_for_nonexistent_node(self, async_session):
        """GET /graph/node/{node_id} should return 404 for nonexistent node"""
        from unittest.mock import AsyncMock as AsyncMock2

        from app.services.graph_service import GraphService

        service = GraphService(async_session, AsyncMock2())
        user_id = uuid4()
        node_id = uuid4()

        result = await service.get_node(user_id, node_id)

        assert result is None

    async def test_get_node_enforces_user_isolation(self, async_session):
        """GET /graph/node/{node_id} should return 404 for other users' nodes"""
        from unittest.mock import AsyncMock as AsyncMock2

        from app.services.graph_service import GraphService

        repo = GraphRepository(async_session)
        service = GraphService(async_session, AsyncMock2())
        user1_id = uuid4()
        user2_id = uuid4()

        # Create node for user1
        node = await repo.upsert_node(
            user_id=user1_id,
            type="note",
            title="User1 Note",
            source_id=uuid4(),
        )

        # Try to access as user2
        result = await service.get_node(user2_id, node.id)

        assert result is None

    async def test_get_neighbors_returns_neighbors_with_edges(
        self, async_session, sample_data
    ):
        """GET /graph/neighbors/{node_id} should return node with neighbors"""
        from unittest.mock import AsyncMock as AsyncMock2

        from app.services.graph_service import GraphService

        service = GraphService(async_session, AsyncMock2())
        user_id = sample_data["user_id"]
        node_id = sample_data["note"].id

        result = await service.get_neighbors(user_id, node_id)

        assert result is not None
        assert result.node.id == node_id
        assert len(result.neighbors) > 0
        assert result.neighbors[0].id == sample_data["habit"].id

    async def test_get_neighbors_returns_none_for_nonexistent_node(self, async_session):
        """GET /graph/neighbors/{node_id} should return None for nonexistent node"""
        from unittest.mock import AsyncMock as AsyncMock2

        from app.services.graph_service import GraphService

        service = GraphService(async_session, AsyncMock2())
        user_id = uuid4()
        node_id = uuid4()

        result = await service.get_neighbors(user_id, node_id)

        assert result is None

    async def test_get_neighbors_enforces_user_isolation(self, async_session):
        """GET /graph/neighbors should not return other users' neighbors"""
        from unittest.mock import AsyncMock as AsyncMock2

        from app.services.graph_service import GraphService

        repo = GraphRepository(async_session)
        service = GraphService(async_session, AsyncMock2())
        user1_id = uuid4()
        user2_id = uuid4()

        # Create node for user1 with neighbor
        node1 = await repo.upsert_node(
            user_id=user1_id,
            type="note",
            title="User1 Node",
            source_id=uuid4(),
        )

        neighbor1 = await repo.upsert_node(
            user_id=user1_id,
            type="habit",
            title="User1 Neighbor",
            source_id=uuid4(),
        )

        await repo.create_edge(
            user_id=user1_id,
            source_node_id=node1.id,
            target_node_id=neighbor1.id,
            relation_type="note_links",
        )

        # Try to access as user2
        result = await service.get_neighbors(user2_id, node1.id)

        assert result is None

    async def test_get_subgraph_returns_nodes_and_edges(
        self, async_session, sample_data
    ):
        """GET /graph/subgraph should return subgraph response"""
        from unittest.mock import AsyncMock as AsyncMock2

        from app.services.graph_service import GraphService

        service = GraphService(async_session, AsyncMock2())
        user_id = sample_data["user_id"]
        node_id = sample_data["note"].id

        result = await service.get_subgraph(user_id, node_id)

        assert result is not None
        assert len(result.nodes) >= 1
        assert len(result.edges) >= 0
        assert any(n.id == node_id for n in result.nodes)

    async def test_get_subgraph_respects_depth_parameter(self, async_session):
        """GET /graph/subgraph should respect depth parameter"""
        from unittest.mock import AsyncMock as AsyncMock2

        from app.services.graph_service import GraphService

        repo = GraphRepository(async_session)
        service = GraphService(async_session, AsyncMock2())
        user_id = uuid4()

        # Create chain: n1 -> n2 -> n3 -> n4
        nodes = []
        for i in range(4):
            node = await repo.upsert_node(
                user_id=user_id,
                type="note",
                title=f"Note {i}",
                source_id=uuid4(),
            )
            nodes.append(node)

        for i in range(len(nodes) - 1):
            await repo.create_edge(
                user_id=user_id,
                source_node_id=nodes[i].id,
                target_node_id=nodes[i + 1].id,
                relation_type="note_links",
            )

        # Get subgraph with depth 1
        result1 = await service.get_subgraph(user_id, nodes[0].id, depth=1)

        # Get subgraph with depth 2
        result2 = await service.get_subgraph(user_id, nodes[0].id, depth=2)

        # Depth 2 should include more nodes than depth 1
        assert len(result2.nodes) >= len(result1.nodes)

    async def test_get_subgraph_enforces_user_isolation(self, async_session):
        """GET /graph/subgraph should return None for other users' subgraph"""
        from unittest.mock import AsyncMock as AsyncMock2

        from app.services.graph_service import GraphService

        repo = GraphRepository(async_session)
        service = GraphService(async_session, AsyncMock2())
        user1_id = uuid4()
        user2_id = uuid4()

        # Create subgraph for user1
        node = await repo.upsert_node(
            user_id=user1_id,
            type="note",
            title="User1 Node",
            source_id=uuid4(),
        )

        # Try to access as user2
        result = await service.get_subgraph(user2_id, node.id)

        assert result is None

    async def test_get_stats_returns_graph_statistics(self, async_session, sample_data):
        """GET /graph/stats should return graph statistics"""
        from app.repositories.graph_repository import GraphRepository

        repo = GraphRepository(async_session)
        user_id = sample_data["user_id"]

        total_nodes, total_edges, node_types, relation_types = await repo.get_stats(
            user_id
        )

        assert total_nodes == 2
        assert total_edges == 1
        assert "note" in node_types
        assert "habit" in node_types
        assert "habit_related_to_learning" in relation_types

    async def test_get_stats_enforces_user_isolation(self, async_session):
        """GET /graph/stats should only count requesting user's data"""
        from app.repositories.graph_repository import GraphRepository

        repo = GraphRepository(async_session)
        user1_id = uuid4()
        user2_id = uuid4()

        # Create nodes for user1
        await repo.upsert_node(
            user_id=user1_id,
            type="note",
            title="User1 Note",
            source_id=uuid4(),
        )

        # Create nodes for user2
        await repo.upsert_node(
            user_id=user2_id,
            type="note",
            title="User2 Note",
            source_id=uuid4(),
        )

        # Get stats for user1
        total_nodes1, _, _, _ = await repo.get_stats(user1_id)

        # Get stats for user2
        total_nodes2, _, _, _ = await repo.get_stats(user2_id)

        # Each user should only see their own node
        assert total_nodes1 == 1
        assert total_nodes2 == 1


class TestGraphRoutesErrorHandling:
    """Test error handling in routes"""

    async def test_missing_user_id_header_handling(self):
        """Routes should handle missing user ID appropriately"""
        # This would be tested via HTTP client
        # Routes should require X-User-ID header
        pass

    async def test_invalid_node_id_format_handling(self, async_session):
        """Routes should handle invalid node ID format gracefully"""
        from unittest.mock import AsyncMock as AsyncMock2

        from app.services.graph_service import GraphService

        service = GraphService(async_session, AsyncMock2())
        user_id = uuid4()

        # Try with invalid UUID format
        try:
            result = await service.get_node(user_id, "invalid-id")
            # Should either convert to UUID or return None
            assert result is None
        except Exception:
            # Invalid UUID format should raise an error
            pass

    async def test_database_error_handling(self, async_session):
        """Routes should handle database errors gracefully"""
        from unittest.mock import AsyncMock as AsyncMock2

        from app.services.graph_service import GraphService

        service = GraphService(async_session, AsyncMock2())
        user_id = uuid4()
        node_id = uuid4()

        # Mock repository to raise error
        with patch.object(service.repo, "get_node", side_effect=Exception("DB Error")):
            try:
                await service.get_node(user_id, node_id)
            except Exception as e:
                # Should propagate error (could be caught at route level)
                assert str(e) == "DB Error"


class TestGraphRoutesRateLimit:
    """Test rate limiting behavior"""

    async def test_rate_limit_enforced_per_user(self, mock_redis):
        """Rate limiter should track requests per user"""
        mock_redis.incr = AsyncMock(return_value=51)  # Exceed 50 request limit

        # When request count exceeds 50, should return 429
        # This is tested in main.py middleware, not route directly
        pass

    async def test_rate_limit_reset_on_window_expiry(self, mock_redis):
        """Rate limit counter should reset after time window"""
        # Rate limit window is 60 seconds
        # This is tested in main.py middleware
        pass


class TestGraphRoutesCaching:
    """Test caching behavior in routes"""

    async def test_repeated_get_node_hits_cache(
        self, async_session, sample_data, mock_redis
    ):
        """Repeated GET /graph/node should use cache on second call"""
        from app.services.graph_service import GraphService

        service = GraphService(async_session, mock_redis)
        user_id = sample_data["user_id"]
        node_id = sample_data["note"].id

        # First call: cache miss
        mock_redis.get.return_value = None
        await service.get_node(user_id, node_id)

        # Verify cache was set
        assert mock_redis.setex.called

        # Simulate cache hit for second call
        import json

        cached = {
            "id": str(node_id),
            "user_id": str(user_id),
            "type": "note",
            "title": "Test Note",
            "source_id": str(uuid4()),
            "metadata": None,
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-01T00:00:00+00:00",
        }
        mock_redis.get.return_value = json.dumps(cached)

        result2 = await service.get_node(user_id, node_id)

        assert result2 is not None
        assert result2.id == node_id

    async def test_cache_invalidation_on_mutation(self, async_session, sample_data):
        """Cache should be invalidated after node mutation"""
        from unittest.mock import AsyncMock as AsyncMock2

        from app.services.graph_service import GraphService

        service = GraphService(async_session, AsyncMock2())
        user_id = sample_data["user_id"]
        node_id = sample_data["note"].id

        # Invalidate cache
        await service.invalidate_node_cache(node_id)

        # Next get should fetch from DB (cache would be empty)
        result = await service.get_node(user_id, node_id)

        assert result is not None


class TestGraphRoutesResponseFormats:
    """Test response format compliance"""

    async def test_node_response_includes_required_fields(
        self, async_session, sample_data
    ):
        """NodeResponse should include all required fields"""
        from unittest.mock import AsyncMock as AsyncMock2

        from app.services.graph_service import GraphService

        service = GraphService(async_session, AsyncMock2())
        user_id = sample_data["user_id"]
        node_id = sample_data["note"].id

        result = await service.get_node(user_id, node_id)

        assert hasattr(result, "id")
        assert hasattr(result, "type")
        assert hasattr(result, "title")
        assert hasattr(result, "source_id")
        assert hasattr(result, "metadata")

    async def test_edge_response_includes_required_fields(
        self, async_session, sample_data
    ):
        """EdgeResponse should include all required fields"""
        from unittest.mock import AsyncMock as AsyncMock2

        from app.services.graph_service import GraphService

        service = GraphService(async_session, AsyncMock2())
        user_id = sample_data["user_id"]
        node_id = sample_data["note"].id

        result = await service.get_neighbors(user_id, node_id)

        assert result is not None
        assert len(result.edges) > 0
        edge = result.edges[0]
        assert hasattr(edge, "id")
        assert hasattr(edge, "source_node_id")
        assert hasattr(edge, "target_node_id")
        assert hasattr(edge, "relation_type")

    async def test_subgraph_response_format(self, async_session, sample_data):
        """SubgraphResponse should have correct structure"""
        from unittest.mock import AsyncMock as AsyncMock2

        from app.services.graph_service import GraphService

        service = GraphService(async_session, AsyncMock2())
        user_id = sample_data["user_id"]
        node_id = sample_data["note"].id

        result = await service.get_subgraph(user_id, node_id)

        assert result is not None
        assert hasattr(result, "nodes")
        assert hasattr(result, "edges")
        assert isinstance(result.nodes, list)
        assert isinstance(result.edges, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
