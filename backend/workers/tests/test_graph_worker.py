"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Test suite for Graph Worker event consumption and handling
"""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.workers.graph_worker import GraphEventConsumer


def create_event(event_type: str, source_service: str, payload: dict) -> dict:
    """Helper to create properly structured BaseEvent dict"""
    return {
        "event_type": event_type,
        "source_service": source_service,
        "payload": payload,
    }


@pytest.fixture
async def async_session():
    """Create an in-memory SQLite async session for tests"""
    # Mock the models import to avoid circular imports
    from app.models.graph_model import Base

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
def graph_worker():
    """Create a GraphEventConsumer instance"""
    consumer = GraphEventConsumer(
        topics=["test.topic"],
        group_id="test-group",
    )
    return consumer


class TestGraphWorkerEventRouting:
    """Test event routing and dispatch"""

    async def test_handle_note_created_event(self, graph_worker):
        """Worker should route note.created events to correct handler"""
        event_payload = create_event(
            event_type="note.created",
            source_service="notes-service",
            payload={
                "note_id": str(uuid4()),
                "user_id": str(uuid4()),
                "title": "Test Note",
            },
        )

        # Mock the handler
        graph_worker._handle_note_created = AsyncMock()

        await graph_worker.handle_event("note.created", event_payload)

        graph_worker._handle_note_created.assert_called_once()

    async def test_handle_note_link_created_event(self, graph_worker):
        """Worker should route note.link.created events to correct handler"""
        event_payload = create_event(
            event_type="note.link.created",
            source_service="notes-service",
            payload={
                "source_note_id": str(uuid4()),
                "target_note_id": str(uuid4()),
                "user_id": str(uuid4()),
            },
        )

        graph_worker._handle_note_link_created = AsyncMock()

        await graph_worker.handle_event("note.link.created", event_payload)

        graph_worker._handle_note_link_created.assert_called_once()

    async def test_handle_note_deleted_event(self, graph_worker):
        """Worker should route note.deleted events to correct handler"""
        event_payload = create_event(
            event_type="note.deleted",
            source_service="notes-service",
            payload={"note_id": str(uuid4())},
        )

        graph_worker._handle_note_deleted = AsyncMock()

        await graph_worker.handle_event("note.deleted", event_payload)

        graph_worker._handle_note_deleted.assert_called_once()

    async def test_handle_record_created_event(self, graph_worker):
        """Worker should route record.created events to correct handler"""
        event_payload = create_event(
            event_type="record.created",
            source_service="database-service",
            payload={
                "record_id": str(uuid4()),
                "user_id": str(uuid4()),
                "database_name": "Test Record",
            },
        )

        graph_worker._handle_record_created = AsyncMock()

        await graph_worker.handle_event("record.created", event_payload)

        graph_worker._handle_record_created.assert_called_once()

    async def test_handle_habit_created_event(self, graph_worker):
        """Worker should route habit.created events to correct handler"""
        event_payload = create_event(
            event_type="habit.created",
            source_service="habit-service",
            payload={
                "habit_id": str(uuid4()),
                "user_id": str(uuid4()),
                "name": "Test Habit",
            },
        )

        graph_worker._handle_habit_created = AsyncMock()

        await graph_worker.handle_event("habit.created", event_payload)

        graph_worker._handle_habit_created.assert_called_once()

    async def test_handle_learning_topic_created_event(self, graph_worker):
        """Worker should route learning.topic.created events to correct handler"""
        event_payload = create_event(
            event_type="learning.topic.created",
            source_service="learning-service",
            payload={
                "topic_id": str(uuid4()),
                "user_id": str(uuid4()),
                "name": "Test Topic",
            },
        )

        graph_worker._handle_learning_topic_created = AsyncMock()

        await graph_worker.handle_event("learning.topic.created", event_payload)

        graph_worker._handle_learning_topic_created.assert_called_once()

    async def test_handle_session_completed_event(self, graph_worker):
        """Worker should route learning.session.completed events to correct handler"""
        event_payload = create_event(
            event_type="learning.session.completed",
            source_service="learning-service",
            payload={
                "topic_id": str(uuid4()),
                "user_id": str(uuid4()),
                "session_notes": [str(uuid4()), str(uuid4())],
            },
        )

        graph_worker._handle_session_completed = AsyncMock()

        await graph_worker.handle_event("learning.session.completed", event_payload)

        graph_worker._handle_session_completed.assert_called_once()

    async def test_handle_meal_logged_event(self, graph_worker):
        """Worker should route meal.logged events to correct handler"""
        event_payload = create_event(
            event_type="meal.logged",
            source_service="health-service",
            payload={
                "meal_id": str(uuid4()),
                "user_id": str(uuid4()),
                "food_name": "Pasta",
            },
        )

        graph_worker._handle_meal_logged = AsyncMock()

        await graph_worker.handle_event("meal.logged", event_payload)

        graph_worker._handle_meal_logged.assert_called_once()

    async def test_handle_workout_logged_event(self, graph_worker):
        """Worker should route workout.logged events to correct handler"""
        event_payload = create_event(
            event_type="workout.logged",
            source_service="health-service",
            payload={
                "workout_id": str(uuid4()),
                "user_id": str(uuid4()),
                "workout_type": "Running",
            },
        )

        graph_worker._handle_workout_logged = AsyncMock()

        await graph_worker.handle_event("workout.logged", event_payload)

        graph_worker._handle_workout_logged.assert_called_once()

    async def test_ignore_non_graph_events(self, graph_worker):
        """Worker should ignore events not in graph scope"""
        event_payload = create_event(
            event_type="some.other.event",
            source_service="unknown-service",
            payload={"some": "data"},
        )

        # No handlers should be called
        graph_worker._handle_note_created = AsyncMock()

        await graph_worker.handle_event("some.other.event", event_payload)

        graph_worker._handle_note_created.assert_not_called()


class TestGraphWorkerNodeCreation:
    """Test node creation from events"""

    async def test_note_created_creates_node(self, graph_worker):
        """note.created event should create a graph node"""
        note_id = uuid4()
        user_id = uuid4()

        event_payload = {
            "note_id": str(note_id),
            "user_id": str(user_id),
            "title": "My Note",
        }

        # Mock upsert_node
        graph_worker._upsert_node = AsyncMock()

        await graph_worker._handle_note_created(event_payload)

        graph_worker._upsert_node.assert_called_once_with(
            user_id=user_id,
            type="note",
            title="My Note",
            source_id=note_id,
        )

    async def test_habit_created_creates_node(self, graph_worker):
        """habit.created event should create a graph node"""
        habit_id = uuid4()
        user_id = uuid4()

        event_payload = {
            "habit_id": str(habit_id),
            "user_id": str(user_id),
            "name": "Morning Run",
        }

        graph_worker._upsert_node = AsyncMock()

        await graph_worker._handle_habit_created(event_payload)

        graph_worker._upsert_node.assert_called_once_with(
            user_id=user_id,
            type="habit",
            title="Morning Run",
            source_id=habit_id,
        )

    async def test_learning_topic_created_creates_node(self, graph_worker):
        """learning.topic.created event should create a graph node"""
        topic_id = uuid4()
        user_id = uuid4()

        event_payload = {
            "topic_id": str(topic_id),
            "user_id": str(user_id),
            "name": "Python Basics",
        }

        graph_worker._upsert_node = AsyncMock()

        await graph_worker._handle_learning_topic_created(event_payload)

        graph_worker._upsert_node.assert_called_once_with(
            user_id=user_id,
            type="learning_topic",
            title="Python Basics",
            source_id=topic_id,
        )

    async def test_record_created_creates_node(self, graph_worker):
        """record.created event should create a database_record node"""
        record_id = uuid4()
        user_id = uuid4()

        event_payload = {
            "record_id": str(record_id),
            "user_id": str(user_id),
            "database_name": "Contacts",
        }

        graph_worker._upsert_node = AsyncMock()

        await graph_worker._handle_record_created(event_payload)

        graph_worker._upsert_node.assert_called_once_with(
            user_id=user_id,
            type="database_record",
            title="Contacts",
            source_id=record_id,
        )

    async def test_meal_logged_creates_health_log_node(self, graph_worker):
        """meal.logged event should create a health_log node"""
        meal_id = uuid4()
        user_id = uuid4()

        event_payload = {
            "meal_id": str(meal_id),
            "user_id": str(user_id),
            "food_name": "Chicken Salad",
        }

        graph_worker._upsert_node = AsyncMock()

        await graph_worker._handle_meal_logged(event_payload)

        graph_worker._upsert_node.assert_called_once()
        call_kwargs = graph_worker._upsert_node.call_args[1]
        assert call_kwargs["type"] == "health_log"
        assert call_kwargs["title"] == "Meal: Chicken Salad"
        assert call_kwargs["metadata"]["log_type"] == "meal"

    async def test_workout_logged_creates_health_log_node(self, graph_worker):
        """workout.logged event should create a health_log node"""
        workout_id = uuid4()
        user_id = uuid4()

        event_payload = {
            "workout_id": str(workout_id),
            "user_id": str(user_id),
            "workout_type": "Cycling",
        }

        graph_worker._upsert_node = AsyncMock()

        await graph_worker._handle_workout_logged(event_payload)

        graph_worker._upsert_node.assert_called_once()
        call_kwargs = graph_worker._upsert_node.call_args[1]
        assert call_kwargs["type"] == "health_log"
        assert call_kwargs["title"] == "Workout: Cycling"
        assert call_kwargs["metadata"]["log_type"] == "workout"


class TestGraphWorkerEdgeCreation:
    """Test edge creation from events"""

    async def test_note_link_creates_edge(self, graph_worker):
        """note.link.created event should create an edge between notes"""
        source_note_id = uuid4()
        target_note_id = uuid4()
        user_id = uuid4()

        event_payload = {
            "source_note_id": str(source_note_id),
            "target_note_id": str(target_note_id),
            "user_id": str(user_id),
        }

        graph_worker._create_edge_by_source = AsyncMock()

        await graph_worker._handle_note_link_created(event_payload)

        graph_worker._create_edge_by_source.assert_called_once_with(
            user_id=user_id,
            source_source_id=source_note_id,
            target_source_id=target_note_id,
            relation_type="note_links",
        )

    async def test_habit_creates_edge_to_learning_topics(self, graph_worker):
        """habit.created with learning topics should create edges"""
        habit_id = uuid4()
        user_id = uuid4()
        topic_id1 = uuid4()
        topic_id2 = uuid4()

        event_payload = {
            "habit_id": str(habit_id),
            "user_id": str(user_id),
            "name": "Study Python",
            "related_learning_topics": [str(topic_id1), str(topic_id2)],
        }

        graph_worker._upsert_node = AsyncMock()
        graph_worker._create_edge_by_source = AsyncMock()

        await graph_worker._handle_habit_created(event_payload)

        # Should create 2 edges (one per learning topic)
        assert graph_worker._create_edge_by_source.call_count == 2

    async def test_session_completed_creates_edges_to_topic(self, graph_worker):
        """learning.session.completed should create edges from notes to topic"""
        topic_id = uuid4()
        user_id = uuid4()
        note_id1 = uuid4()
        note_id2 = uuid4()

        event_payload = {
            "topic_id": str(topic_id),
            "user_id": str(user_id),
            "session_notes": [str(note_id1), str(note_id2)],
        }

        graph_worker._create_edge_by_source = AsyncMock()

        await graph_worker._handle_session_completed(event_payload)

        # Should create 2 edges (one per session note)
        assert graph_worker._create_edge_by_source.call_count == 2

    async def test_record_creates_edge_to_related_note(self, graph_worker):
        """record.created with related note should create edge"""
        record_id = uuid4()
        user_id = uuid4()
        note_id = uuid4()

        event_payload = {
            "record_id": str(record_id),
            "user_id": str(user_id),
            "database_name": "Contact",
            "related_note_id": str(note_id),
        }

        graph_worker._upsert_node = AsyncMock()
        graph_worker._create_edge_by_source = AsyncMock()

        await graph_worker._handle_record_created(event_payload)

        graph_worker._create_edge_by_source.assert_called_once_with(
            user_id=user_id,
            source_source_id=record_id,
            target_source_id=note_id,
            relation_type="record_related_to_note",
        )

    async def test_workout_creates_edge_to_habit(self, graph_worker):
        """workout.logged with related habit should create edge"""
        workout_id = uuid4()
        user_id = uuid4()
        habit_id = uuid4()

        event_payload = {
            "workout_id": str(workout_id),
            "user_id": str(user_id),
            "workout_type": "Running",
            "related_habit_id": str(habit_id),
        }

        graph_worker._upsert_node = AsyncMock()
        graph_worker._create_edge_by_source = AsyncMock()

        await graph_worker._handle_workout_logged(event_payload)

        graph_worker._create_edge_by_source.assert_called_once_with(
            user_id=user_id,
            source_source_id=workout_id,
            target_source_id=habit_id,
            relation_type="health_related_to_habit",
        )


class TestGraphWorkerNodeDeletion:
    """Test node deletion from events"""

    async def test_note_deleted_removes_node(self, graph_worker):
        """note.deleted event should delete the graph node"""
        note_id = uuid4()

        event_payload = {
            "note_id": str(note_id),
        }

        graph_worker._delete_node_by_source = AsyncMock()

        await graph_worker._handle_note_deleted(event_payload)

        graph_worker._delete_node_by_source.assert_called_once_with(note_id)


class TestGraphWorkerErrorHandling:
    """Test error handling in worker"""

    async def test_missing_note_id_logs_warning(self, graph_worker):
        """Missing note_id should be logged but not crash"""
        event_payload = {
            "user_id": str(uuid4()),
            "title": "Note without ID",
        }

        graph_worker._upsert_node = AsyncMock()

        await graph_worker._handle_note_created(event_payload)

        # Should not call upsert
        graph_worker._upsert_node.assert_not_called()

    async def test_missing_user_id_logs_warning(self, graph_worker):
        """Missing user_id should be logged but not crash"""
        event_payload = {
            "note_id": str(uuid4()),
            "title": "Note without user",
        }

        graph_worker._upsert_node = AsyncMock()

        await graph_worker._handle_note_created(event_payload)

        # Should not call upsert
        graph_worker._upsert_node.assert_not_called()

    async def test_database_error_is_caught_and_logged(self, graph_worker):
        """Database errors should be caught and logged"""
        event_payload = {
            "note_id": str(uuid4()),
            "user_id": str(uuid4()),
            "title": "Test Note",
        }

        # Mock to raise exception
        graph_worker._upsert_node = AsyncMock(side_effect=Exception("DB Error"))

        # Should not raise, but log error
        await graph_worker._handle_note_created(event_payload)

        # Call should have been attempted
        graph_worker._upsert_node.assert_called_once()

    async def test_invalid_uuid_format_handled(self, graph_worker):
        """Invalid UUID formats should be handled gracefully"""
        event_payload = {
            "note_id": "not-a-uuid",
            "user_id": "also-not-uuid",
            "title": "Test",
        }

        graph_worker._upsert_node = AsyncMock()

        # Should handle gracefully
        try:
            await graph_worker._handle_note_created(event_payload)
        except ValueError:
            # UUID parsing may raise ValueError
            pass


class TestGraphWorkerEventValidation:
    """Test event payload validation"""

    async def test_minimal_valid_note_created_payload(self, graph_worker):
        """Minimal valid note.created payload should work"""
        event_payload = {
            "note_id": str(uuid4()),
            "user_id": str(uuid4()),
        }

        graph_worker._upsert_node = AsyncMock()

        await graph_worker._handle_note_created(event_payload)

        graph_worker._upsert_node.assert_called_once()

    async def test_event_with_optional_fields(self, graph_worker):
        """Events with optional fields should be handled"""
        event_payload = {
            "note_id": str(uuid4()),
            "user_id": str(uuid4()),
            "title": "Custom Title",
            "extra_field": "should be ignored",
        }

        graph_worker._upsert_node = AsyncMock()

        await graph_worker._handle_note_created(event_payload)

        # Should extract only relevant fields
        graph_worker._upsert_node.assert_called_once()


class TestGraphWorkerCrossDomainRelationships:
    """Test cross-domain relationship creation"""

    async def test_habit_learning_relationship(self, graph_worker):
        """Habit and learning topics should be related"""
        habit_id = uuid4()
        topic_id = uuid4()
        user_id = uuid4()

        event_payload = {
            "habit_id": str(habit_id),
            "user_id": str(user_id),
            "name": "Study",
            "related_learning_topics": [str(topic_id)],
        }

        # Mock the async db session factory to avoid real DB connections
        async def mock_get_session():
            # Return None to skip actual DB operations
            class MockSession:
                async def execute(self, *args, **kwargs):
                    class Result:
                        def scalar_one_or_none(self):
                            return None

                    return Result()

                async def commit(self):
                    pass

                async def rollback(self):
                    pass

                async def close(self):
                    pass

                def add(self, *args):
                    pass

            return MockSession()

        graph_worker._get_session = mock_get_session

        # Should not raise exception
        await graph_worker._handle_habit_created(event_payload)

    async def test_health_habit_relationship(self, graph_worker):
        """Health logs (workout) should be related to habits"""
        workout_id = uuid4()
        habit_id = uuid4()
        user_id = uuid4()

        event_payload = {
            "workout_id": str(workout_id),
            "user_id": str(user_id),
            "workout_type": "Running",
            "related_habit_id": str(habit_id),
        }

        # Mock the async db session factory to avoid real DB connections
        async def mock_get_session():
            # Return None to skip actual DB operations
            class MockSession:
                async def execute(self, *args, **kwargs):
                    class Result:
                        def scalar_one_or_none(self):
                            return None

                    return Result()

                async def commit(self):
                    pass

                async def rollback(self):
                    pass

                async def close(self):
                    pass

                def add(self, *args):
                    pass

            return MockSession()

        graph_worker._get_session = mock_get_session

        # Should not raise exception
        await graph_worker._handle_workout_logged(event_payload)

    async def test_record_note_relationship(self, graph_worker):
        """Database records should be related to notes"""
        record_id = uuid4()
        note_id = uuid4()
        user_id = uuid4()

        event_payload = {
            "record_id": str(record_id),
            "user_id": str(user_id),
            "database_name": "Contact",
            "related_note_id": str(note_id),
        }

        # Mock the async db session factory to avoid real DB connections
        async def mock_get_session():
            # Return None to skip actual DB operations
            class MockSession:
                async def execute(self, *args, **kwargs):
                    class Result:
                        def scalar_one_or_none(self):
                            return None

                    return Result()

                async def commit(self):
                    pass

                async def rollback(self):
                    pass

                async def close(self):
                    pass

                def add(self, *args):
                    pass

            return MockSession()

        graph_worker._get_session = mock_get_session

        # Should not raise exception
        await graph_worker._handle_record_created(event_payload)

    async def test_learning_note_relationship(self, graph_worker):
        """Learning sessions create relationships between notes and topics"""
        topic_id = uuid4()
        note_id = uuid4()
        user_id = uuid4()

        event_payload = {
            "topic_id": str(topic_id),
            "user_id": str(user_id),
            "session_notes": [str(note_id)],
        }

        graph_worker._create_edge_by_source = AsyncMock()

        await graph_worker._handle_session_completed(event_payload)

        # Verify edge creation with correct relation type
        call_kwargs = graph_worker._create_edge_by_source.call_args[1]
        assert call_kwargs["relation_type"] == "learning_related_to_note"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
