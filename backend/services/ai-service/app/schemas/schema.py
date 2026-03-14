"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AIPromptRequest(BaseModel):
    interaction_type: str = Field(..., description="recommendation, summary, assistant")
    prompt: str = Field(..., min_length=1)
    metadata_json: Optional[dict[str, Any]] = None


class AIResponse(BaseModel):
    id: UUID
    user_id: UUID
    interaction_type: str
    prompt: str
    response: str
    metadata_json: Optional[dict[str, Any]]
    created_at: datetime

    model_config = {"from_attributes": True}


class AIInteractionListResponse(BaseModel):
    interactions: list[AIResponse]
    total: int
