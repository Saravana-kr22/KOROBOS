"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Search Worker

Consumes note events and upserts documents into the notes Meilisearch index.
"""

import asyncio
import json
from typing import Any
from urllib import error, request

from backend.shared.config.settings import get_settings
from backend.shared.logging.logger import get_logger
from backend.shared.messaging.consumer import BaseEventConsumer
from backend.shared.messaging.schemas import BaseEvent
from backend.workers.event_transforms import (
    search_document_from_habit_payload,
    search_document_from_health_payload,
    search_document_from_learning_payload,
    search_document_from_payload,
    search_document_from_record_payload,
)
from backend.workers.topics import SEARCH_TOPICS

logger = get_logger("search-worker")
settings = get_settings()


class SearchEventConsumer(BaseEventConsumer):
    """Consumer that maintains the notes search index from note events."""

    async def handle_event(self, topic: str, payload: dict[str, Any]):
        event = BaseEvent.model_validate(payload)

        # Handle note events
        if event.event_type in {"note.created", "note.updated"}:
            document = search_document_from_payload(event.payload)
            await asyncio.to_thread(self._upsert_documents, [document], "notes")
        elif event.event_type == "note.deleted":
            note_id = event.payload.get("note_id")
            if note_id:
                await asyncio.to_thread(self._delete_document, note_id, "notes")

        # Handle database record events
        elif event.event_type in {"record.created", "record.updated"}:
            document = search_document_from_record_payload(event.payload)
            await asyncio.to_thread(self._upsert_documents, [document], "records")
        elif event.event_type == "record.deleted":
            record_id = event.payload.get("record_id")
            if record_id:
                await asyncio.to_thread(self._delete_document, record_id, "records")

        # Handle learning events
        elif event.event_type in {
            "learning.session.logged",
            "learning.session.completed",
        }:
            document = search_document_from_learning_payload(
                event.event_type, event.payload
            )
            await asyncio.to_thread(self._upsert_documents, [document], "learning")
        elif event.event_type == "learning.topic.created":
            document = search_document_from_learning_payload(
                event.event_type, event.payload
            )
            await asyncio.to_thread(self._upsert_documents, [document], "learning")

        # Handle habit events
        elif event.event_type == "habit.created":
            document = search_document_from_habit_payload(event.payload)
            await asyncio.to_thread(self._upsert_documents, [document], "habits")

        # Handle health events (meals and workouts)
        elif event.event_type in {"meal.logged", "workout.logged"}:
            document = search_document_from_health_payload(
                event.event_type, event.payload
            )
            await asyncio.to_thread(self._upsert_documents, [document], "health")

        else:
            logger.debug("Ignoring non-search event_type: %s", event.event_type)

    def _upsert_documents(
        self, documents: list[dict[str, Any]], index_name: str = "notes"
    ) -> None:
        base_url = settings.search_url.rstrip("/")
        target_url = f"{base_url}/indexes/{index_name}/documents?primaryKey=id"
        payload = json.dumps(documents).encode("utf-8")

        headers = {"Content-Type": "application/json"}
        if settings.search_api_key:
            headers["Authorization"] = f"Bearer {settings.search_api_key}"

        req = request.Request(
            target_url,
            data=payload,
            headers=headers,
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=10) as response:
                if response.status >= 400:
                    raise RuntimeError(
                        f"Search index update failed with status {response.status}"
                    )
                logger.info(
                    f"Upserted {len(documents)} documents to {index_name} index"
                )
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(
                f"Search index update failed with status {exc.code}: {detail}"
            ) from exc

    def _delete_document(self, doc_id: str, index_name: str = "notes") -> None:
        """Remove a document from the Meilisearch index by its ID."""
        base_url = settings.search_url.rstrip("/")
        target_url = f"{base_url}/indexes/{index_name}/documents/{doc_id}"

        headers = {}
        if settings.search_api_key:
            headers["Authorization"] = f"Bearer {settings.search_api_key}"

        req = request.Request(target_url, headers=headers, method="DELETE")
        try:
            with request.urlopen(req, timeout=10) as response:
                if response.status >= 400:
                    raise RuntimeError(
                        f"Search index delete failed with status {response.status}"
                    )
                logger.info(f"Deleted {doc_id} from {index_name} index")
        except error.HTTPError as exc:
            if exc.code == 404:
                logger.debug(
                    "Document %s not in %s index, skipping delete",
                    doc_id,
                    index_name,
                )
                return
            detail = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(
                f"Search index delete failed with status {exc.code}: {detail}"
            ) from exc


async def main() -> None:
    consumer = SearchEventConsumer(
        topics=list(SEARCH_TOPICS),
        group_id="search-group",
    )
    await consumer.start()

    logger.info("Search worker started")
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Search worker shutting down")
        await consumer.stop()


if __name__ == "__main__":
    asyncio.run(main())
