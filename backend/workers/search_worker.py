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
from backend.workers.event_transforms import search_document_from_payload
from backend.workers.topics import SEARCH_TOPICS

logger = get_logger("search-worker")
settings = get_settings()


class SearchEventConsumer(BaseEventConsumer):
    """Consumer that maintains the notes search index from note events."""

    async def handle_event(self, topic: str, payload: dict[str, Any]):
        event = BaseEvent.model_validate(payload)

        if event.event_type in {"note.created", "note.updated"}:
            document = search_document_from_payload(event.payload)
            await asyncio.to_thread(self._upsert_documents, [document])
        elif event.event_type == "note.deleted":
            note_id = event.payload.get("note_id")
            if note_id:
                await asyncio.to_thread(self._delete_document, note_id)
        else:
            logger.debug("Ignoring non-search event_type: %s", event.event_type)

    def _upsert_documents(self, documents: list[dict[str, Any]]) -> None:
        base_url = settings.search_url.rstrip("/")
        target_url = f"{base_url}/indexes/notes/documents?primaryKey=id"
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
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(
                f"Search index update failed with status {exc.code}: {detail}"
            ) from exc

    def _delete_document(self, note_id: str) -> None:
        """Remove a note from the Meilisearch index by its ID."""
        base_url = settings.search_url.rstrip("/")
        target_url = f"{base_url}/indexes/notes/documents/{note_id}"

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
        except error.HTTPError as exc:
            if exc.code == 404:
                logger.debug(
                    "Document %s not in search index, skipping delete", note_id
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
