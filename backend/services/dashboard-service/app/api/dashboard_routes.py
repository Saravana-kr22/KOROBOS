"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Dashboard Service API routes.
"""

from uuid import UUID

from app.api.rate_limit import check_dashboard_rate_limit
from app.schemas.dashboard_schema import DailyMetrics, OverviewResponse, WeeklyResponse
from app.services.dashboard_service import DashboardService
from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.database.connection import get_db_session

router = APIRouter()


def _get_user_id(x_user_id: str = Header(..., alias="X-User-ID")) -> UUID:
    """Extract user ID from X-User-ID header (injected by gateway)."""
    return UUID(x_user_id)


@router.get(
    "/overview",
    response_model=OverviewResponse,
    tags=["Dashboard"],
    dependencies=[Depends(check_dashboard_rate_limit)],
)
async def get_overview(
    request: Request,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get dashboard overview (summary card).

    Returns simplified metrics: habits_completed, learning_minutes,
    calories_balance, productivity_score.
    """
    from app.config.settings import get_settings
    from app.main import DASHBOARD_REQUESTS

    settings = get_settings()
    redis = getattr(request.app.state, "redis", None)
    svc = DashboardService(session, settings, redis)

    # Extract auth headers
    headers = {"X-User-ID": str(user_id)}
    if "authorization" in request.headers:
        headers["Authorization"] = request.headers["authorization"]

    result = await svc.get_overview(user_id, headers)

    # Increment metrics
    DASHBOARD_REQUESTS.labels(endpoint="overview").inc()

    return result


@router.get(
    "/daily",
    response_model=DailyMetrics,
    tags=["Dashboard"],
    dependencies=[Depends(check_dashboard_rate_limit)],
)
async def get_daily(
    request: Request,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get full daily metrics breakdown.

    Returns complete DailyMetrics: habits_completed, learning_minutes,
    calories_consumed/burned/net, productivity_score.
    """
    from app.config.settings import get_settings
    from app.main import DASHBOARD_REQUESTS

    settings = get_settings()
    redis = getattr(request.app.state, "redis", None)
    svc = DashboardService(session, settings, redis)

    # Extract auth headers
    headers = {"X-User-ID": str(user_id)}
    if "authorization" in request.headers:
        headers["Authorization"] = request.headers["authorization"]

    result = await svc.get_daily(user_id, headers)

    # Increment metrics
    DASHBOARD_REQUESTS.labels(endpoint="daily").inc()

    return result


@router.get(
    "/weekly",
    response_model=WeeklyResponse,
    tags=["Dashboard"],
    dependencies=[Depends(check_dashboard_rate_limit)],
)
async def get_weekly(
    request: Request,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get weekly trends (7-day aggregated metrics).

    Returns last 7 days of daily metrics + aggregate statistics
    (avg_productivity_score, total_learning_minutes, etc).
    """
    from app.config.settings import get_settings
    from app.main import DASHBOARD_REQUESTS

    settings = get_settings()
    redis = getattr(request.app.state, "redis", None)
    svc = DashboardService(session, settings, redis)

    # Extract auth headers
    headers = {"X-User-ID": str(user_id)}
    if "authorization" in request.headers:
        headers["Authorization"] = request.headers["authorization"]

    result = await svc.get_weekly(user_id, headers)

    # Increment metrics
    DASHBOARD_REQUESTS.labels(endpoint="weekly").inc()

    return result


@router.get(
    "/metrics",
    response_model=DailyMetrics,
    tags=["Dashboard"],
    dependencies=[Depends(check_dashboard_rate_limit)],
)
async def get_metrics(
    request: Request,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get detailed metrics (same as /daily with full breakdown).

    Returns complete DailyMetrics for detailed dashboard view.
    """
    from app.config.settings import get_settings
    from app.main import DASHBOARD_REQUESTS

    settings = get_settings()
    redis = getattr(request.app.state, "redis", None)
    svc = DashboardService(session, settings, redis)

    # Extract auth headers
    headers = {"X-User-ID": str(user_id)}
    if "authorization" in request.headers:
        headers["Authorization"] = request.headers["authorization"]

    result = await svc.get_daily(user_id, headers)

    # Increment metrics
    DASHBOARD_REQUESTS.labels(endpoint="metrics").inc()

    return result
