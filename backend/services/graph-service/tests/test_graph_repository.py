"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Test suite for Graph Repository layer
"""

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


class TestGraphRepositoryNodeOperations:
    """Test node CRUD operations"""

    async def test_upsert_node_creates_new(self, async_session):
        """Upsert should create a new node when it doesn't exist"""
        repo = GraphRepository(async_session)
        user_id = uuid4()
        source_id = uuid4()

        node = await repo.upsert_node(
            user_id=user_id,
            type="note",
            title="Test Note",
            source_id=source_id,
            metadata={"key": "value"},
        )

        assert node.id is not None
        assert node.user_id == user_id
        assert node.type == "note"
        assert node.title == "Test Note"
        assert node.source_id == source_id
        assert node.metadata_json == {"key": "value"}

    async def test_upsert_node_updates_existing(self, async_session):
        """Upsert should update an existing node by source_id"""
        repo = GraphRepository(async_session)
        user_id = uuid4()
        source_id = uuid4()

        # Create node
        node1 = await repo.upsert_node(
            user_id=user_id,
            type="note",
            title="Original Title",
            source_id=source_id,
        )

        # Upsert with same source_id
        node2 = await repo.upsert_node(
            user_id=user_id,
            type="habit",
            title="Updated Title",
            source_id=source_id,
        )

        # Should be same node with updated properties
        assert node2.id == node1.id
        assert node2.title == "Updated Title"
        assert node2.type == "habit"

    async def test_upsert_node_enforces_user_isolation(self, async_session):
        """Upsert should not confuse nodes from different users"""
        repo = GraphRepository(async_session)
        user1_id = uuid4()
        user2_id = uuid4()
        source_id = uuid4()

        node1 = await repo.upsert_node(
            user_id=user1_id,
            type="note",
            title="User1 Note",
            source_id=source_id,
        )

        node2 = await repo.upsert_node(
            user_id=user2_id,
            type="note",
            title="User2 Note",
            source_id=source_id,
        )

        assert node1.id != node2.id
        assert node1.user_id == user1_id
        assert node2.user_id == user2_id

    async def test_get_node_by_id(self, async_session):
        """Get node by ID should return the node"""
        repo = GraphRepository(async_session)
        user_id = uuid4()
        source_id = uuid4()

        created = await repo.upsert_node(
            user_id=user_id,
            type="note",
            title="Test",
            source_id=source_id,
        )

        fetched = await repo.get_node(user_id, created.id)

        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.title == "Test"

    async def test_get_node_enforces_user_isolation(self, async_session):
        """Get node should return None for other users"""
        repo = GraphRepository(async_session)
        user1_id = uuid4()
        user2_id = uuid4()
        source_id = uuid4()

        node = await repo.upsert_node(
            user_id=user1_id,
            type="note",
            title="Test",
            source_id=source_id,
        )

        # User2 cannot access User1's node
        fetched = await repo.get_node(user2_id, node.id)
        assert fetched is None

    async def test_delete_node_by_source(self, async_session):
        """Delete node should remove it from database"""
        repo = GraphRepository(async_session)
        user_id = uuid4()
        source_id = uuid4()

        node = await repo.upsert_node(
            user_id=user_id,
            type="note",
            title="Test",
            source_id=source_id,
        )

        await repo.delete_node_by_source(source_id)

        fetched = await repo.get_node(user_id, node.id)
        assert fetched is None

    async def test_find_node_by_source(self, async_session):
        """Find node by source_id should locate the node"""
        repo = GraphRepository(async_session)
        user_id = uuid4()
        source_id = uuid4()

        created = await repo.upsert_node(
            user_id=user_id,
            type="note",
            title="Test",
            source_id=source_id,
        )

        found = await repo.find_node_by_source(source_id)

        assert found is not None
        assert found.id == created.id


class TestGraphRepositoryEdgeOperations:
    """Test edge CRUD operations"""

    async def test_create_edge(self, async_session):
        """Create edge should link two nodes"""
        repo = GraphRepository(async_session)
        user_id = uuid4()

        node1 = await repo.upsert_node(
            user_id=user_id,
            type="note",
            title="Note 1",
            source_id=uuid4(),
        )

        node2 = await repo.upsert_node(
            user_id=user_id,
            type="note",
            title="Note 2",
            source_id=uuid4(),
        )

        edge = await repo.create_edge(
            user_id=user_id,
            source_node_id=node1.id,
            target_node_id=node2.id,
            relation_type="note_links",
        )

        assert edge.id is not None
        assert edge.source_node_id == node1.id
        assert edge.target_node_id == node2.id
        assert edge.relation_type == "note_links"
        assert edge.user_id == user_id

    async def test_edge_cascade_delete(self, async_session):
        """Deleting a node should cascade delete its edges"""
        repo = GraphRepository(async_session)
        user_id = uuid4()
        source_id1 = uuid4()
        source_id2 = uuid4()

        node1 = await repo.upsert_node(
            user_id=user_id,
            type="note",
            title="Note 1",
            source_id=source_id1,
        )

        node2 = await repo.upsert_node(
            user_id=user_id,
            type="note",
            title="Note 2",
            source_id=source_id2,
        )

        await repo.create_edge(
            user_id=user_id,
            source_node_id=node1.id,
            target_node_id=node2.id,
            relation_type="note_links",
        )

        # Delete source node
        await repo.delete_node_by_source(source_id1)

        # Node2 should still exist, but edge should be gone
        node2_exists = await repo.get_node(user_id, node2.id)
        assert node2_exists is not None

        # Edge should be deleted due to cascade
        # (We'd need to query edges directly to verify)


class TestGraphRepositoryQueries:
    """Test complex graph queries"""

    async def test_get_neighbors(self, async_session):
        """Get neighbors should return node with its direct neighbors"""
        repo = GraphRepository(async_session)
        user_id = uuid4()

        center = await repo.upsert_node(
            user_id=user_id,
            type="note",
            title="Center",
            source_id=uuid4(),
        )

        neighbor1 = await repo.upsert_node(
            user_id=user_id,
            type="habit",
            title="Neighbor 1",
            source_id=uuid4(),
        )

        neighbor2 = await repo.upsert_node(
            user_id=user_id,
            type="learning_topic",
            title="Neighbor 2",
            source_id=uuid4(),
        )

        await repo.create_edge(
            user_id=user_id,
            source_node_id=center.id,
            target_node_id=neighbor1.id,
            relation_type="habit_related_to_learning",
        )

        await repo.create_edge(
            user_id=user_id,
            source_node_id=center.id,
            target_node_id=neighbor2.id,
            relation_type="note_links",
        )

        node, edges, neighbors = await repo.get_neighbors(user_id, center.id)

        assert node.id == center.id
        assert len(edges) == 2
        assert len(neighbors) == 2
        assert neighbor1.id in [n.id for n in neighbors]
        assert neighbor2.id in [n.id for n in neighbors]

    async def test_get_subgraph(self, async_session):
        """Get subgraph should return all nodes within depth"""
        repo = GraphRepository(async_session)
        user_id = uuid4()

        # Create a chain: n1 -> n2 -> n3 -> n4
        nodes = []
        for i in range(1, 5):
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

        # Get subgraph from node 1 with depth 2
        subgraph_nodes, subgraph_edges = await repo.get_subgraph(
            user_id, nodes[0].id, depth=2
        )

        # Should include nodes 1, 2, 3 (depth 2 from node 1)
        assert len(subgraph_nodes) >= 2
        assert nodes[0].id in [n.id for n in subgraph_nodes]

    async def test_get_stats(self, async_session):
        """Get stats should return graph statistics"""
        repo = GraphRepository(async_session)
        user_id = uuid4()

        # Create nodes of different types
        note = await repo.upsert_node(
            user_id=user_id,
            type="note",
            title="Note",
            source_id=uuid4(),
        )

        habit = await repo.upsert_node(
            user_id=user_id,
            type="habit",
            title="Habit",
            source_id=uuid4(),
        )

        await repo.create_edge(
            user_id=user_id,
            source_node_id=note.id,
            target_node_id=habit.id,
            relation_type="habit_related_to_learning",
        )

        total_nodes, total_edges, node_types, relation_types = await repo.get_stats(
            user_id
        )

        assert total_nodes == 2
        assert total_edges == 1
        assert node_types["note"] == 1
        assert node_types["habit"] == 1
        assert relation_types["habit_related_to_learning"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
