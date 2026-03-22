"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Graph Worker — Sprint 14

Consumes events from Notes, Habits, Learning, and Database services
and maintains the knowledge graph in PostgreSQL.

Pipeline:
    Event Bus → Graph Worker → Graph Repository → PostgreSQL

Event handlers map cross-domain entities to graph nodes and relationships.
"""

import asyncio
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.shared.config.settings import get_settings
from backend.shared.logging.logger import get_logger
from backend.shared.messaging.consumer import BaseEventConsumer
from backend.shared.messaging.schemas import BaseEvent
from backend.workers.topics import GRAPH_TOPICS

logger = get_logger("graph-worker")
settings = get_settings()


class GraphEventConsumer(BaseEventConsumer):
    """Consumer that maintains the knowledge graph in PostgreSQL."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._session_factory = None

    async def _get_session(self) -> AsyncSession:
        """Get or create async session factory."""
        if self._session_factory is None:
            engine = create_async_engine(
                settings.database_url,
                echo=False,
                pool_size=5,
                max_overflow=10,
            )
            self._session_factory = sessionmaker(
                engine, class_=AsyncSession, expire_on_commit=False
            )

        return self._session_factory()

    async def handle_event(self, topic: str, payload: dict[str, Any]):
        event = BaseEvent.model_validate(payload)

        # Route to appropriate handler
        if event.event_type == "note.created":
            await self._handle_note_created(event.payload)
        elif event.event_type == "note.link.created":
            await self._handle_note_link_created(event.payload)
        elif event.event_type == "note.deleted":
            await self._handle_note_deleted(event.payload)
        elif event.event_type == "record.created":
            await self._handle_record_created(event.payload)
        elif event.event_type == "habit.created":
            await self._handle_habit_created(event.payload)
        elif event.event_type == "learning.topic.created":
            await self._handle_learning_topic_created(event.payload)
        elif event.event_type == "learning.session.completed":
            await self._handle_session_completed(event.payload)
        elif event.event_type == "meal.logged":
            await self._handle_meal_logged(event.payload)
        elif event.event_type == "workout.logged":
            await self._handle_workout_logged(event.payload)
        else:
            logger.debug("Ignoring non-graph event: %s", event.event_type)

    async def _handle_note_created(self, payload: dict[str, Any]) -> None:
        """Create a note node in the graph."""
        note_id = payload.get("note_id")
        user_id = payload.get("user_id")
        title = payload.get("title", "Untitled Note")

        if not note_id or not user_id:
            logger.warning("note.created missing IDs: %s", payload)
            return

        try:
            await self._upsert_node(
                user_id=UUID(user_id),
                type="note",
                title=title,
                source_id=UUID(note_id),
            )
        except Exception as exc:
            logger.error("Failed to create note node: %s", exc)

    async def _handle_note_link_created(self, payload: dict[str, Any]) -> None:
        """Create an edge between two note nodes."""
        source_id = payload.get("source_note_id")
        target_id = payload.get("target_note_id")
        user_id = payload.get("user_id")

        if not source_id or not target_id or not user_id:
            logger.warning("note.link.created missing IDs: %s", payload)
            return

        try:
            await self._create_edge_by_source(
                user_id=UUID(user_id),
                source_source_id=UUID(source_id),
                target_source_id=UUID(target_id),
                relation_type="note_links",
            )
        except Exception as exc:
            logger.error("Failed to create note link edge: %s", exc)

    async def _handle_note_deleted(self, payload: dict[str, Any]) -> None:
        """Delete a note node from the graph."""
        note_id = payload.get("note_id")

        if not note_id:
            logger.warning("note.deleted missing note_id: %s", payload)
            return

        try:
            await self._delete_node_by_source(UUID(note_id))
        except Exception as exc:
            logger.error("Failed to delete note node: %s", exc)

    async def _handle_record_created(self, payload: dict[str, Any]) -> None:
        """Create a database record node in the graph."""
        record_id = payload.get("record_id")
        user_id = payload.get("user_id")
        database_name = payload.get("database_name", "Record")

        if not record_id or not user_id:
            logger.warning("record.created missing IDs: %s", payload)
            return

        try:
            await self._upsert_node(
                user_id=UUID(user_id),
                type="database_record",
                title=database_name,
                source_id=UUID(record_id),
            )

            # Create edge to related note if provided
            note_id = payload.get("related_note_id")
            if note_id:
                await self._create_edge_by_source(
                    user_id=UUID(user_id),
                    source_source_id=UUID(record_id),
                    target_source_id=UUID(note_id),
                    relation_type="record_related_to_note",
                )
        except Exception as exc:
            logger.error("Failed to create record node: %s", exc)

    async def _handle_habit_created(self, payload: dict[str, Any]) -> None:
        """Create a habit node in the graph."""
        habit_id = payload.get("habit_id")
        user_id = payload.get("user_id")
        name = payload.get("name", "Habit")

        if not habit_id or not user_id:
            logger.warning("habit.created missing IDs: %s", payload)
            return

        try:
            await self._upsert_node(
                user_id=UUID(user_id),
                type="habit",
                title=name,
                source_id=UUID(habit_id),
            )

            # Create edge to learning topics if provided
            learning_topic_ids = payload.get("related_learning_topics", [])
            for topic_id in learning_topic_ids:
                await self._create_edge_by_source(
                    user_id=UUID(user_id),
                    source_source_id=UUID(habit_id),
                    target_source_id=UUID(topic_id),
                    relation_type="habit_related_to_learning",
                )
        except Exception as exc:
            logger.error("Failed to create habit node: %s", exc)

    async def _handle_learning_topic_created(self, payload: dict[str, Any]) -> None:
        """Create a learning topic node in the graph."""
        topic_id = payload.get("topic_id")
        user_id = payload.get("user_id")
        name = payload.get("name", "Topic")

        if not topic_id or not user_id:
            logger.warning("learning.topic.created missing IDs: %s", payload)
            return

        try:
            await self._upsert_node(
                user_id=UUID(user_id),
                type="learning_topic",
                title=name,
                source_id=UUID(topic_id),
            )
        except Exception as exc:
            logger.error("Failed to create learning topic node: %s", exc)

    async def _handle_session_completed(self, payload: dict[str, Any]) -> None:
        """Create edges between session notes and the learning topic."""
        topic_id = payload.get("topic_id")
        user_id = payload.get("user_id")
        session_notes = payload.get("session_notes", [])

        if not topic_id or not user_id:
            logger.warning("learning.session.completed missing IDs: %s", payload)
            return

        try:
            # Create edges from each session note to the topic
            for note_id in session_notes:
                await self._create_edge_by_source(
                    user_id=UUID(user_id),
                    source_source_id=UUID(note_id),
                    target_source_id=UUID(topic_id),
                    relation_type="learning_related_to_note",
                )
        except Exception as exc:
            logger.error("Failed to create session edges: %s", exc)

    async def _upsert_node(
        self,
        user_id: UUID,
        type: str,
        title: str,
        source_id: UUID,
        metadata: dict | None = None,
    ) -> None:
        """Upsert a node in the graph database."""
        # Import here to avoid circular imports
        from sqlalchemy import and_, select

        from backend.services.graph_service.app.models.graph_model import GraphNode

        session = await self._get_session()
        try:
            # Check if node exists
            result = await session.execute(
                select(GraphNode).where(
                    and_(GraphNode.user_id == user_id, GraphNode.source_id == source_id)
                )
            )
            node = result.scalar_one_or_none()

            if node:
                # Update existing
                node.type = type
                node.title = title
                if metadata:
                    node.metadata_json = metadata
            else:
                # Create new
                node = GraphNode(
                    user_id=user_id,
                    type=type,
                    title=title,
                    source_id=source_id,
                    metadata_json=metadata,
                )
                session.add(node)

            await session.commit()
            logger.debug("Node upserted: %s (%s)", source_id, type)
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def _delete_node_by_source(self, source_id: UUID) -> None:
        """Delete a node by source_id."""
        from sqlalchemy import select

        from backend.services.graph_service.app.models.graph_model import GraphNode

        session = await self._get_session()
        try:
            result = await session.execute(
                select(GraphNode).where(GraphNode.source_id == source_id)
            )
            node = result.scalar_one_or_none()
            if node:
                await session.delete(node)
                await session.commit()
                logger.debug("Node deleted: %s", source_id)
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def _create_edge_by_source(
        self,
        user_id: UUID,
        source_source_id: UUID,
        target_source_id: UUID,
        relation_type: str,
    ) -> None:
        """Create an edge between two nodes identified by source_id."""
        from sqlalchemy import and_, select

        from backend.services.graph_service.app.models.graph_model import (
            GraphEdge,
            GraphNode,
        )

        session = await self._get_session()
        try:
            # Find source and target nodes by source_id
            source_result = await session.execute(
                select(GraphNode).where(
                    and_(
                        GraphNode.user_id == user_id,
                        GraphNode.source_id == source_source_id,
                    )
                )
            )
            source_node = source_result.scalar_one_or_none()

            target_result = await session.execute(
                select(GraphNode).where(
                    and_(
                        GraphNode.user_id == user_id,
                        GraphNode.source_id == target_source_id,
                    )
                )
            )
            target_node = target_result.scalar_one_or_none()

            if source_node and target_node:
                # Create edge
                edge = GraphEdge(
                    user_id=user_id,
                    source_node_id=source_node.id,
                    target_node_id=target_node.id,
                    relation_type=relation_type,
                )
                session.add(edge)
                await session.commit()
                logger.debug(
                    "Edge created: %s -[%s]-> %s",
                    source_source_id,
                    relation_type,
                    target_source_id,
                )
            else:
                logger.warning(
                    "Could not create edge: source_node=%s, target_node=%s",
                    source_node,
                    target_node,
                )
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def _handle_meal_logged(self, payload: dict[str, Any]) -> None:
        """Create a health log node for a meal."""
        meal_id = payload.get("meal_id")
        user_id = payload.get("user_id")
        food_name = payload.get("food_name", "Meal")

        if not meal_id or not user_id:
            logger.warning("meal.logged missing IDs: %s", payload)
            return

        try:
            await self._upsert_node(
                user_id=UUID(user_id),
                type="health_log",
                title=f"Meal: {food_name}",
                source_id=UUID(meal_id),
                metadata={"log_type": "meal"},
            )
        except Exception as exc:
            logger.error("Failed to create meal node: %s", exc)

    async def _handle_workout_logged(self, payload: dict[str, Any]) -> None:
        """Create a health log node for a workout."""
        workout_id = payload.get("workout_id")
        user_id = payload.get("user_id")
        workout_type = payload.get("workout_type", "Workout")

        if not workout_id or not user_id:
            logger.warning("workout.logged missing IDs: %s", payload)
            return

        try:
            await self._upsert_node(
                user_id=UUID(user_id),
                type="health_log",
                title=f"Workout: {workout_type}",
                source_id=UUID(workout_id),
                metadata={"log_type": "workout"},
            )

            # Create edge from workout to habit if habit_id provided
            habit_id = payload.get("related_habit_id")
            if habit_id:
                await self._create_edge_by_source(
                    user_id=UUID(user_id),
                    source_source_id=UUID(workout_id),
                    target_source_id=UUID(habit_id),
                    relation_type="health_related_to_habit",
                )
        except Exception as exc:
            logger.error("Failed to create workout node: %s", exc)

    async def stop(self):
        await super().stop()


async def main() -> None:
    consumer = GraphEventConsumer(
        topics=list(GRAPH_TOPICS),
        group_id="graph-group",
    )
    await consumer.start()

    logger.info("Graph worker started")
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Graph worker shutting down")
        await consumer.stop()


if __name__ == "__main__":
    asyncio.run(main())
