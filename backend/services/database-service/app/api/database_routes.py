"""
KOROBOS — Database Service Routes

API endpoints for database, property, and record operations.
"""

import logging
from datetime import date
from typing import Optional
from uuid import UUID

from app.api.rate_limit import check_write_rate_limit
from app.models.database_model import Database
from app.models.record_model import Record
from app.schemas.database_schema import (
    DatabaseCreate,
    DatabaseListResponse,
    DatabaseResponse,
    DatabaseStatsResponse,
    DatabaseUpdate,
    PropertyCreate,
    PropertyResponse,
    RecordCreate,
    RecordFilter,
    RecordListResponse,
    RecordResponse,
    RecordSort,
    RecordUpdate,
)
from app.services.database_service import DatabaseService
from app.services.record_service import RecordService
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.database.connection import get_db_session

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_user_id(x_user_id: str = Header(..., alias="X-User-ID")) -> UUID:
    """Extract and validate user ID from gateway header.

    Args:
        x_user_id: User ID from X-User-ID header (injected by gateway)

    Returns:
        UUID

    Raises:
        HTTPException: 422 if header missing or invalid
    """
    try:
        return UUID(x_user_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid X-User-ID header")


# ============================================================================
# Database Endpoints
# ============================================================================


@router.post(
    "/databases",
    response_model=DatabaseResponse,
    status_code=201,
    tags=["Databases"],
)
async def create_database(
    data: DatabaseCreate,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
    request: Request = None,
) -> DatabaseResponse:
    """Create a new database.

    Args:
        data: Database creation data
        user_id: User creating the database
        session: Database session
        request: FastAPI request

    Returns:
        Created DatabaseResponse
    """
    svc = DatabaseService(
        session, getattr(request.app.state, "redis", None) if request else None
    )
    db = await svc.create_database(user_id, data)
    await session.commit()
    return DatabaseResponse.model_validate(db)


@router.get(
    "/databases",
    response_model=DatabaseListResponse,
    tags=["Databases"],
)
async def list_databases(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
    request: Request = None,
) -> DatabaseListResponse:
    """List databases for the authenticated user.

    Args:
        page: Page number (1-indexed)
        limit: Results per page
        user_id: Authenticated user ID
        session: Database session
        request: FastAPI request

    Returns:
        DatabaseListResponse with paginated databases
    """
    svc = DatabaseService(
        session, getattr(request.app.state, "redis", None) if request else None
    )
    databases, total = await svc.list_databases(user_id, page, limit)

    pages = (total + limit - 1) // limit
    return DatabaseListResponse(
        databases=[DatabaseResponse.model_validate(db) for db in databases],
        total=total,
        page=page,
        limit=limit,
        pages=pages,
    )


@router.get(
    "/stats",
    response_model=DatabaseStatsResponse,
    tags=["Databases"],
)
async def get_database_stats(
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
) -> DatabaseStatsResponse:
    """Get database and record statistics for the user."""
    today = date.today()

    # Total databases count
    db_result = await session.execute(
        select(func.count(Database.id)).where(Database.user_id == user_id)
    )
    total_databases = db_result.scalar() or 0

    # Records created today (across all user's databases)
    record_result = await session.execute(
        select(func.count(Record.id)).where(
            Record.database_id.in_(
                select(Database.id).where(Database.user_id == user_id)
            ),
            func.date(Record.created_at) == today,
        )
    )
    records_created_today = record_result.scalar() or 0

    return {
        "total_databases": total_databases,
        "records_created_today": records_created_today,
    }


@router.get(
    "/databases/{db_id}",
    response_model=DatabaseResponse,
    tags=["Databases"],
)
async def get_database(
    db_id: UUID,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
    request: Request = None,
) -> DatabaseResponse:
    """Fetch a specific database by ID.

    Args:
        db_id: Database ID
        user_id: Authenticated user ID
        session: Database session
        request: FastAPI request

    Returns:
        DatabaseResponse

    Raises:
        HTTPException: 404 if database not found or doesn't belong to user
    """
    svc = DatabaseService(
        session, getattr(request.app.state, "redis", None) if request else None
    )
    db = await svc.get_database(db_id)

    if not db or db.user_id != user_id:
        raise HTTPException(status_code=404, detail="Database not found")

    return DatabaseResponse.model_validate(db)


@router.put(
    "/databases/{db_id}",
    response_model=DatabaseResponse,
    tags=["Databases"],
)
async def update_database(
    db_id: UUID,
    data: DatabaseUpdate,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
    request: Request = None,
) -> DatabaseResponse:
    """Update a database.

    Args:
        db_id: Database ID
        data: Update data
        user_id: Authenticated user ID
        session: Database session
        request: FastAPI request

    Returns:
        Updated DatabaseResponse

    Raises:
        HTTPException: 404 if database not found or doesn't belong to user
    """
    svc = DatabaseService(
        session, getattr(request.app.state, "redis", None) if request else None
    )
    db = await svc.get_database(db_id)

    if not db or db.user_id != user_id:
        raise HTTPException(status_code=404, detail="Database not found")

    db = await svc.update_database(db, data)
    await session.commit()

    return DatabaseResponse.model_validate(db)


@router.delete(
    "/databases/{db_id}",
    status_code=204,
    tags=["Databases"],
)
async def delete_database(
    db_id: UUID,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
    request: Request = None,
) -> None:
    """Delete a database.

    Args:
        db_id: Database ID
        user_id: Authenticated user ID
        session: Database session
        request: FastAPI request

    Raises:
        HTTPException: 404 if database not found or doesn't belong to user
    """
    svc = DatabaseService(
        session, getattr(request.app.state, "redis", None) if request else None
    )
    db = await svc.get_database(db_id)

    if not db or db.user_id != user_id:
        raise HTTPException(status_code=404, detail="Database not found")

    await svc.delete_database(db)
    await session.commit()


# ============================================================================
# Property Endpoints
# ============================================================================


@router.post(
    "/databases/{db_id}/properties",
    response_model=PropertyResponse,
    status_code=201,
    tags=["Properties"],
)
async def add_property(
    db_id: UUID,
    data: PropertyCreate,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
    request: Request = None,
) -> PropertyResponse:
    """Add a property to a database.

    Args:
        db_id: Database ID
        data: Property creation data
        user_id: Authenticated user ID
        session: Database session
        request: FastAPI request

    Returns:
        Created PropertyResponse

    Raises:
        HTTPException: 404 if database not found or doesn't belong to user
    """
    svc = DatabaseService(
        session, getattr(request.app.state, "redis", None) if request else None
    )
    db = await svc.get_database(db_id)

    if not db or db.user_id != user_id:
        raise HTTPException(status_code=404, detail="Database not found")

    prop = await svc.add_property(db_id, data)
    await session.commit()

    return PropertyResponse.model_validate(prop)


@router.delete(
    "/databases/{db_id}/properties/{prop_id}",
    status_code=204,
    tags=["Properties"],
)
async def delete_property(
    db_id: UUID,
    prop_id: UUID,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
    request: Request = None,
) -> None:
    """Delete a property from a database.

    Args:
        db_id: Database ID
        prop_id: Property ID
        user_id: Authenticated user ID
        session: Database session
        request: FastAPI request

    Raises:
        HTTPException: 404 if database or property not found
    """
    svc = DatabaseService(
        session, getattr(request.app.state, "redis", None) if request else None
    )
    db = await svc.get_database(db_id)

    if not db or db.user_id != user_id:
        raise HTTPException(status_code=404, detail="Database not found")

    prop = await svc.prop_repo.get_by_id(prop_id)
    if not prop or prop.database_id != db_id:
        raise HTTPException(status_code=404, detail="Property not found")

    await svc.delete_property(prop)
    await session.commit()


# ============================================================================
# Record Endpoints
# ============================================================================


@router.post(
    "/databases/{db_id}/records",
    response_model=RecordResponse,
    status_code=201,
    tags=["Records"],
)
async def create_record(
    db_id: UUID,
    data: RecordCreate,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
    request: Request = None,
) -> RecordResponse:
    """Create a new record.

    Args:
        db_id: Database ID
        data: Record creation data
        user_id: Authenticated user ID
        session: Database session
        request: FastAPI request

    Returns:
        Created RecordResponse

    Raises:
        HTTPException: 400 if validation fails
        HTTPException: 404 if database not found
        HTTPException: 429 if rate limit exceeded
    """
    # Check ownership
    db_svc = DatabaseService(
        session, getattr(request.app.state, "redis", None) if request else None
    )
    db = await db_svc.get_database(db_id)

    if not db or db.user_id != user_id:
        raise HTTPException(status_code=404, detail="Database not found")

    # Check rate limit
    await check_write_rate_limit(request, user_id)

    # Create record with validation
    try:
        rec_svc = RecordService(session)
        record = await rec_svc.create_record(db_id, user_id, data)
        await session.commit()
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Validation error: {str(e)}",
        )

    return RecordResponse.model_validate(record)


@router.get(
    "/databases/{db_id}/records",
    response_model=RecordListResponse,
    tags=["Records"],
)
async def list_records(
    db_id: UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    filter_property_id: Optional[list[UUID]] = Query(None),
    filter_operator: Optional[list[str]] = Query(None),
    filter_value: Optional[list[str]] = Query(None),
    sort_property_id: Optional[UUID] = Query(None),
    sort_direction: str = Query("asc"),
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
    request: Request = None,
) -> RecordListResponse:
    """List records for a database with optional filtering and sorting.

    Supports multiple filters combined with AND logic.

    Example: ?filter_property_id=prop1&filter_operator=eq&filter_value=value1
             &filter_property_id=prop2&filter_operator=contains&filter_value=value2

    Args:
        db_id: Database ID
        page: Page number (1-indexed)
        limit: Results per page
        filter_property_id: Property ID(s) to filter by (can repeat)
        filter_operator: Filter operator(s) (eq, contains, gt, lt, gte, lte)
        filter_value: Filter value(s) (can repeat, match order of property_id)
        sort_property_id: Property to sort by
        sort_direction: Sort direction (asc, desc)
        user_id: Authenticated user ID
        session: Database session
        request: FastAPI request

    Returns:
        RecordListResponse with paginated records

    Raises:
        HTTPException: 404 if database not found
        HTTPException: 422 if filter parameters don't match
    """
    # Check ownership
    db_svc = DatabaseService(
        session, getattr(request.app.state, "redis", None) if request else None
    )
    db = await db_svc.get_database(db_id)

    if not db or db.user_id != user_id:
        raise HTTPException(status_code=404, detail="Database not found")

    # Build filters - validate parameter counts match
    filters = []
    if filter_property_id:
        # Ensure all arrays have same length
        operators = filter_operator or ["eq"] * len(filter_property_id)
        values = filter_value or [None] * len(filter_property_id)

        if len(operators) != len(filter_property_id) or len(values) != len(
            filter_property_id
        ):
            raise HTTPException(
                status_code=422,
                detail="Filter parameters must have matching lengths: "
                "filter_property_id, filter_operator, filter_value",
            )

        for prop_id, op, val in zip(filter_property_id, operators, values):
            if val is not None and val != "":  # Only add filter if value provided
                filters.append(
                    RecordFilter(
                        property_id=prop_id,
                        operator=op,
                        value=val,
                    )
                )

    # Build sort
    sort = None
    if sort_property_id:
        sort = RecordSort(
            property_id=sort_property_id,
            direction=sort_direction,
        )

    # Query records
    rec_svc = RecordService(session)
    records, total = await rec_svc.list_records(
        db_id, filters=filters, sort=sort, page=page, limit=limit
    )

    pages = (total + limit - 1) // limit
    return RecordListResponse(
        records=[RecordResponse.model_validate(r) for r in records],
        total=total,
        page=page,
        limit=limit,
        pages=pages,
    )


@router.put(
    "/records/{record_id}",
    response_model=RecordResponse,
    tags=["Records"],
)
async def update_record(
    record_id: UUID,
    data: RecordUpdate,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
    request: Request = None,
) -> RecordResponse:
    """Update a record.

    Args:
        record_id: Record ID
        data: Update data
        user_id: Authenticated user ID
        session: Database session
        request: FastAPI request

    Returns:
        Updated RecordResponse

    Raises:
        HTTPException: 400 if validation fails
        HTTPException: 404 if record not found
        HTTPException: 429 if rate limit exceeded
    """
    # Check rate limit
    await check_write_rate_limit(request, user_id)

    # Get and validate record
    rec_svc = RecordService(session)
    record = await rec_svc.get_record(record_id)

    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    # Check ownership via database
    db_svc = DatabaseService(
        session, getattr(request.app.state, "redis", None) if request else None
    )
    db = await db_svc.get_database(record.database_id)

    if not db or db.user_id != user_id:
        raise HTTPException(status_code=404, detail="Record not found")

    # Update record with validation
    try:
        record = await rec_svc.update_record(record, user_id, data)
        await session.commit()
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Validation error: {str(e)}",
        )

    return RecordResponse.model_validate(record)


@router.delete(
    "/records/{record_id}",
    status_code=204,
    tags=["Records"],
)
async def delete_record(
    record_id: UUID,
    user_id: UUID = Depends(_get_user_id),
    session: AsyncSession = Depends(get_db_session),
    request: Request = None,
) -> None:
    """Delete a record.

    Args:
        record_id: Record ID
        user_id: Authenticated user ID
        session: Database session
        request: FastAPI request

    Raises:
        HTTPException: 404 if record not found
        HTTPException: 429 if rate limit exceeded
    """
    # Check rate limit
    await check_write_rate_limit(request, user_id)

    # Get and validate record
    rec_svc = RecordService(session)
    record = await rec_svc.get_record(record_id)

    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    # Check ownership via database
    db_svc = DatabaseService(
        session, getattr(request.app.state, "redis", None) if request else None
    )
    db = await db_svc.get_database(record.database_id)

    if not db or db.user_id != user_id:
        raise HTTPException(status_code=404, detail="Record not found")

    # Delete record
    await rec_svc.delete_record(record, user_id)
    await session.commit()
