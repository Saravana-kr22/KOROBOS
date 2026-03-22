"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

AI Service API routes — insights, recommendations, summaries, and prompts.
"""

from datetime import datetime
from uuid import UUID

from app.api.rate_limit import check_ai_rate_limit
from app.config.settings import get_settings
from app.schemas.insight_schema import (
    InsightListResponse,
    RecommendationListResponse,
    SummaryResponse,
)
from app.schemas.schema import AIInteractionListResponse, AIPromptRequest, AIResponse
from app.services.feature_engineering import FeatureEngineeringService
from app.services.insight_service import InsightService
from app.services.recommendation_service import RecommendationService
from app.services.service_logic import AIService
from fastapi import APIRouter, Depends, Header, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.database.connection import get_db_session

router = APIRouter()


def _get_user_id(x_user_id: str = Header(..., alias="X-User-ID")) -> UUID:
    """Extract user ID from X-User-ID header (injected by gateway)."""
    return UUID(x_user_id)


# -- Existing Health Endpoint --


@router.get("/")
async def root():
    return {"message": "AI Service is running"}


# -- Sprint 15 Endpoints: Insights & Recommendations --


@router.get("/insights", response_model=InsightListResponse, tags=["Insights"])
async def get_insights(
    insight_type: str = Query(
        None, description="Filter: behavioral, performance, health, knowledge"
    ),
    limit: int = Query(10, ge=1, le=50),
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
    request: Request = None,
    _: None = Depends(check_ai_rate_limit),
) -> InsightListResponse:
    """Get user's insights with optional type filter."""
    redis = request.app.state.redis if request else None
    settings = get_settings()

    # Create feature engineering and insight services
    feature_svc = FeatureEngineeringService(
        settings.analytics_service_url, settings.graph_service_url
    )
    insight_svc = InsightService(session, redis, settings)

    # Get feature vector
    feature_vector = await feature_svc.get_feature_vector(user_id)

    # Generate insights (will be cached if not already cached)
    await insight_svc.generate_insights(user_id, feature_vector)

    # List insights
    insights, total = await insight_svc.list_insights(user_id, insight_type, limit)

    return InsightListResponse(
        insights=[
            {
                "id": i.id,
                "user_id": i.user_id,
                "insight_type": i.insight_type,
                "text": i.text,
                "confidence": i.confidence,
                "metadata_json": i.metadata_json,
                "created_at": i.created_at,
            }
            for i in insights
        ],
        total=total,
    )


@router.get(
    "/recommendations",
    response_model=RecommendationListResponse,
    tags=["Recommendations"],
)
async def get_recommendations(
    category: str = Query(
        None, description="Filter: habit, learning, health, productivity"
    ),
    limit: int = Query(10, ge=1, le=50),
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
    request: Request = None,
    _: None = Depends(check_ai_rate_limit),
) -> RecommendationListResponse:
    """Get user's recommendations with optional category filter."""
    redis = request.app.state.redis if request else None
    settings = get_settings()

    # Create feature engineering and recommendation services
    feature_svc = FeatureEngineeringService(
        settings.analytics_service_url, settings.graph_service_url
    )
    rec_svc = RecommendationService(session, redis, settings)

    # Get feature vector
    feature_vector = await feature_svc.get_feature_vector(user_id)

    # Generate recommendations
    await rec_svc.generate_recommendations(user_id, feature_vector)

    # List recommendations
    recommendations, total = await rec_svc.list_recommendations(
        user_id, category, limit
    )

    return RecommendationListResponse(
        recommendations=[
            {
                "id": r.id,
                "user_id": r.user_id,
                "category": r.category,
                "text": r.text,
                "priority": r.priority,
                "metadata_json": r.metadata_json,
                "created_at": r.created_at,
            }
            for r in recommendations
        ],
        total=total,
    )


@router.get("/summary", response_model=SummaryResponse, tags=["Summary"])
async def get_summary(
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
    request: Request = None,
    _: None = Depends(check_ai_rate_limit),
) -> SummaryResponse:
    """Get aggregated summary of insights and recommendations."""
    redis = request.app.state.redis if request else None
    settings = get_settings()

    # Create all services
    feature_svc = FeatureEngineeringService(
        settings.analytics_service_url, settings.graph_service_url
    )
    insight_svc = InsightService(session, redis, settings)
    rec_svc = RecommendationService(session, redis, settings)
    ai_svc = AIService(session, redis, settings)

    # Get feature vector
    feature_vector = await feature_svc.get_feature_vector(user_id)

    # Generate insights and recommendations
    await insight_svc.generate_insights(user_id, feature_vector)
    await rec_svc.generate_recommendations(user_id, feature_vector)

    # Get recent insights and recommendations
    insights, _ = await insight_svc.list_insights(user_id, limit=5)
    recommendations, _ = await rec_svc.list_recommendations(user_id, limit=5)

    # Generate natural language summary via Gemini
    summary_prompt = (
        f"I have {len(insights)} insights and {len(recommendations)} "
        f"actionable recommendations. Please provide a 2-3 sentence executive "
        f"summary of my current progress and focus areas."
    )
    summary_request = AIPromptRequest(
        prompt=summary_prompt,
        interaction_type="summary",
    )
    await ai_svc.process_prompt(user_id, summary_request)

    # Get the generated summary
    _, total = await ai_svc.list_interactions(user_id, limit=1)
    interactions, _ = await ai_svc.list_interactions(user_id, limit=1)
    summary_text = (
        interactions[0].response
        if interactions
        else "Summary generation in progress..."
    )

    return SummaryResponse(
        user_id=user_id,
        summary=summary_text,
        generated_at=datetime.utcnow(),
        insights=[
            {
                "id": i.id,
                "user_id": i.user_id,
                "insight_type": i.insight_type,
                "text": i.text,
                "confidence": i.confidence,
                "metadata_json": i.metadata_json,
                "created_at": i.created_at,
            }
            for i in insights
        ],
        recommendations=[
            {
                "id": r.id,
                "user_id": r.user_id,
                "category": r.category,
                "text": r.text,
                "priority": r.priority,
                "metadata_json": r.metadata_json,
                "created_at": r.created_at,
            }
            for r in recommendations
        ],
    )


# -- Existing AI Interaction Endpoints --


@router.post("/prompt", response_model=AIResponse, status_code=201, tags=["Prompts"])
async def create_prompt(
    data: AIPromptRequest,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
    request: Request = None,
    _: None = Depends(check_ai_rate_limit),
) -> AIResponse:
    """Create a prompt and get AI response."""
    redis = request.app.state.redis if request else None
    settings = get_settings()

    svc = AIService(session, redis, settings)
    interaction = await svc.process_prompt(user_id, data)
    await session.commit()

    return AIResponse(
        id=interaction.id,
        user_id=interaction.user_id,
        interaction_type=interaction.interaction_type,
        prompt=interaction.prompt,
        response=interaction.response,
        metadata_json=interaction.metadata_json,
        created_at=interaction.created_at,
    )


@router.get(
    "/interactions", response_model=AIInteractionListResponse, tags=["Interactions"]
)
async def list_interactions(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
    request: Request = None,
    _: None = Depends(check_ai_rate_limit),
) -> AIInteractionListResponse:
    """List user's AI interactions."""
    redis = request.app.state.redis if request else None
    settings = get_settings()

    svc = AIService(session, redis, settings)
    interactions, total = await svc.list_interactions(user_id, offset, limit)

    return AIInteractionListResponse(
        interactions=[
            AIResponse(
                id=i.id,
                user_id=i.user_id,
                interaction_type=i.interaction_type,
                prompt=i.prompt,
                response=i.response,
                metadata_json=i.metadata_json,
                created_at=i.created_at,
            )
            for i in interactions
        ],
        total=total,
    )


@router.get(
    "/interactions/{interaction_id}", response_model=AIResponse, tags=["Interactions"]
)
async def get_interaction(
    interaction_id: UUID,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
    request: Request = None,
    _: None = Depends(check_ai_rate_limit),
) -> AIResponse:
    """Get a specific AI interaction."""
    redis = request.app.state.redis if request else None
    settings = get_settings()

    svc = AIService(session, redis, settings)
    interaction = await svc.get_interaction(interaction_id)

    if not interaction or interaction.user_id != user_id:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Interaction not found")

    return AIResponse(
        id=interaction.id,
        user_id=interaction.user_id,
        interaction_type=interaction.interaction_type,
        prompt=interaction.prompt,
        response=interaction.response,
        metadata_json=interaction.metadata_json,
        created_at=interaction.created_at,
    )
