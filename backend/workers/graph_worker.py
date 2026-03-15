"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Graph Worker — Sprint 6 §16

Consumes note link events and maintains the knowledge graph.

Pipeline:
    Event Bus → Graph Worker → Graph Database

The graph is represented as an adjacency structure persisted in Redis
(sorted sets and hashes) for fast traversal and frontend visualization.
A production deployment would swap Redis for a dedicated graph database
(e.g., Neo4j, ArangoDB), but Redis is sufficient for the current scale
and avoids adding a new infrastructure dependency.

Graph layout in Redis:
    graph:nodes:{note_id}          → HASH  {title, user_id}
    graph:edges:{note_id}:out      → SET   of target_note_ids
    graph:edges:{note_id}:in       → SET   of source_note_ids (backlinks)
"""

import asyncio
from typing import Any

import redis.asyncio as aioredis

from backend.shared.config.settings import get_settings
from backend.shared.logging.logger import get_logger
from backend.shared.messaging.consumer import BaseEventConsumer
from backend.shared.messaging.schemas import BaseEvent
from backend.workers.topics import GRAPH_TOPICS

logger = get_logger("graph-worker")
settings = get_settings()


class GraphEventConsumer(BaseEventConsumer):
    """Consumer that maintains the knowledge graph in Redis."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._redis: aioredis.Redis | None = None

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(settings.redis_url, decode_responses=True)
        return self._redis

    async def handle_event(self, topic: str, payload: dict[str, Any]):
        event = BaseEvent.model_validate(payload)

        if event.event_type == "note.link.created":
            await self._handle_link_created(event.payload)
        elif event.event_type == "note.deleted":
            await self._handle_note_deleted(event.payload)
        else:
            logger.debug("Ignoring non-graph event: %s", event.event_type)

    async def _handle_link_created(self, payload: dict[str, Any]) -> None:
        """Add a directed edge source → target to the graph."""
        source_id = payload.get("source_note_id")
        target_id = payload.get("target_note_id")
        user_id = payload.get("user_id")

        if not source_id or not target_id:
            logger.warning("note.link.created missing IDs: %s", payload)
            return

        r = await self._get_redis()
        pipe = r.pipeline()
        pipe.sadd(f"graph:edges:{source_id}:out", target_id)
        pipe.sadd(f"graph:edges:{target_id}:in", source_id)
        # Store minimal node metadata for graph rendering
        pipe.hset(f"graph:nodes:{source_id}", mapping={"user_id": user_id or ""})
        pipe.hset(f"graph:nodes:{target_id}", mapping={"user_id": user_id or ""})
        await pipe.execute()

        logger.info("Graph edge added: %s → %s", source_id, target_id)

    async def _handle_note_deleted(self, payload: dict[str, Any]) -> None:
        """Remove a node and all its edges from the graph."""
        note_id = payload.get("note_id")
        if not note_id:
            logger.warning("note.deleted missing note_id: %s", payload)
            return

        r = await self._get_redis()

        # Remove outgoing edges and the reverse backlink entries
        out_targets = await r.smembers(f"graph:edges:{note_id}:out")
        in_sources = await r.smembers(f"graph:edges:{note_id}:in")

        pipe = r.pipeline()
        for target_id in out_targets:
            pipe.srem(f"graph:edges:{target_id}:in", note_id)
        for source_id in in_sources:
            pipe.srem(f"graph:edges:{source_id}:out", note_id)
        pipe.delete(f"graph:edges:{note_id}:out")
        pipe.delete(f"graph:edges:{note_id}:in")
        pipe.delete(f"graph:nodes:{note_id}")
        await pipe.execute()

        logger.info("Graph node removed: %s", note_id)

    async def stop(self):
        await super().stop()
        if self._redis:
            await self._redis.close()


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
