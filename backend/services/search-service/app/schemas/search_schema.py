"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Search Service Schemas — request/response models for search endpoints.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class SearchQuery(BaseModel):
    """Unified search query across all domains."""

    q: str = Field(..., description="Search query string")
    type: str | None = Field(
        None,
        description="Filter by type: note, habit, learning, record, meal, workout",
    )
    date_from: datetime | None = Field(
        None, description="Filter results from this date"
    )
    date_to: datetime | None = Field(None, description="Filter results until this date")
    tags: list[str] | None = Field(None, description="Filter notes by tags")
    limit: int = Field(20, ge=1, le=50, description="Max results per page")
    offset: int = Field(0, ge=0, description="Pagination offset")


class SearchResult(BaseModel):
    """A single search result across any domain."""

    id: str = Field(..., description="Unique result ID")
    type: str = Field(
        ..., description="Result type: note, habit, learning, record, meal, workout"
    )
    title: str = Field(..., description="Title or name of the result")
    snippet: str = Field(..., description="Preview/excerpt of the result")
    user_id: str = Field(..., description="Owner user ID")
    score: float | None = Field(None, description="Relevance score from Meilisearch")
    created_at: datetime | None = Field(None, description="When the item was created")


class SearchResponse(BaseModel):
    """Response from a search query."""

    query: str = Field(..., description="The original query string")
    results: list[SearchResult] = Field(..., description="List of search results")
    total: int = Field(..., description="Total number of matching results")
    limit: int = Field(..., description="Limit used in this request")
    offset: int = Field(..., description="Offset used in this request")
    processing_time_ms: int = Field(
        ..., description="Query processing time in milliseconds"
    )


class SuggestResponse(BaseModel):
    """Response from autocomplete/suggest endpoint."""

    query: str = Field(..., description="The partial query string")
    suggestions: list[str] = Field(..., description="List of suggestion strings")
