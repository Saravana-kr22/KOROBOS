"""
CortexOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.
"""

from typing import Optional
from uuid import UUID

from app.models.model import AIInteraction
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


class AIRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: UUID,
        interaction_type: str,
        prompt: str,
        response: str = "",
        metadata_json: dict = None,
    ) -> AIInteraction:
        obj = AIInteraction(
            user_id=user_id,
            interaction_type=interaction_type,
            prompt=prompt,
            response=response,
            metadata_json=metadata_json or {},
        )
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def get_by_id(self, interaction_id: UUID) -> Optional[AIInteraction]:
        result = await self.session.execute(
            select(AIInteraction).where(AIInteraction.id == interaction_id)
        )
        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        user_id: UUID,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[AIInteraction], int]:
        count_q = (
            select(func.count())
            .select_from(AIInteraction)
            .where(AIInteraction.user_id == user_id)
        )
        total = (await self.session.execute(count_q)).scalar_one()
        q = (
            select(AIInteraction)
            .where(AIInteraction.user_id == user_id)
            .order_by(AIInteraction.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(q)
        return list(result.scalars().all()), total

    async def update_response(
        self, interaction: AIInteraction, response: str
    ) -> AIInteraction:
        interaction.response = response
        await self.session.flush()
        return interaction
