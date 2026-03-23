"""
KOROBOS — Database Service Query Engine

Query builder for EAV record filtering and sorting.

The query engine builds SQL queries to filter and sort records stored
in EAV (Entity-Attribute-Value) pattern where values are in the
record_values table.

Pattern:
  - Filtering: correlated EXISTS subquery per filter
  - Sorting: scalar correlated subquery in ORDER BY
  - Pagination: OFFSET/LIMIT
"""

import uuid
from typing import Optional

from app.models.record_model import Record, RecordValue
from app.schemas.database_schema import RecordFilter, RecordSort
from sqlalchemy import Float, and_, case, cast, exists, func, literal, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, joinedload


class QueryEngine:
    """Builds and executes filtered/sorted record queries."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def query_records(
        self,
        database_id: uuid.UUID,
        filters: Optional[list[RecordFilter]] = None,
        sort: Optional[RecordSort] = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[Record], int]:
        """Query records with optional filtering, sorting, and pagination.

        Args:
            database_id: Database ID to query
            filters: List of filter specifications (combined with AND logic)
            sort: Sort specification
            page: Page number (1-indexed)
            limit: Results per page

        Returns:
            Tuple of (records, total_count)
        """
        offset = (page - 1) * limit
        filters = filters or []

        # Count total matching records
        count_stmt = select(func.count()).select_from(Record)
        count_stmt = count_stmt.where(Record.database_id == database_id)

        # Apply filters to count query
        for filter_spec in filters:
            if filter_spec.property_id and filter_spec.value is not None:
                count_stmt = count_stmt.where(self._build_filter_clause(filter_spec))

        total = await self.session.execute(count_stmt)
        total_count = total.scalar_one()

        # Main query: fetch records
        stmt = select(Record).where(Record.database_id == database_id)

        # Apply filters
        for filter_spec in filters:
            if filter_spec.property_id and filter_spec.value is not None:
                stmt = stmt.where(self._build_filter_clause(filter_spec))

        # Apply sorting
        if sort and sort.property_id:
            stmt = self._apply_sort(stmt, sort)
        else:
            stmt = stmt.order_by(Record.created_at.desc())

        # Apply pagination
        stmt = stmt.offset(offset).limit(limit)

        # Eager load values
        stmt = stmt.options(joinedload(Record.values))

        result = await self.session.execute(stmt)
        records = result.scalars().unique().all()

        return list(records), total_count

    def _build_filter_clause(self, filter_spec: RecordFilter):
        """Build a WHERE clause for a single filter using correlated EXISTS.

        Pattern:
            EXISTS (
              SELECT 1 FROM record_values rv
              WHERE rv.record_id = records.id
                AND rv.property_id = :prop_id
                AND <operator_condition>
            )

        Args:
            filter_spec: Filter specification

        Returns:
            SQLAlchemy where() clause
        """
        rv = aliased(RecordValue)

        subq = select(literal(1)).where(
            and_(
                rv.record_id == Record.id,
                rv.property_id == filter_spec.property_id,
            )
        )

        # Apply operator condition
        if filter_spec.operator == "eq":
            subq = subq.where(rv.value == filter_spec.value)
        elif filter_spec.operator == "contains":
            subq = subq.where(rv.value.ilike(f"%{filter_spec.value}%"))
        elif filter_spec.operator == "gt":
            try:
                float_val = float(filter_spec.value)
                subq = subq.where(cast(rv.value, Float) > float_val)
            except (ValueError, TypeError):
                # Non-numeric value for numeric operator
                subq = subq.where(literal(False))
        elif filter_spec.operator == "lt":
            try:
                float_val = float(filter_spec.value)
                subq = subq.where(cast(rv.value, Float) < float_val)
            except (ValueError, TypeError):
                subq = subq.where(literal(False))
        elif filter_spec.operator == "gte":
            try:
                float_val = float(filter_spec.value)
                subq = subq.where(cast(rv.value, Float) >= float_val)
            except (ValueError, TypeError):
                subq = subq.where(literal(False))
        elif filter_spec.operator == "lte":
            try:
                float_val = float(filter_spec.value)
                subq = subq.where(cast(rv.value, Float) <= float_val)
            except (ValueError, TypeError):
                subq = subq.where(literal(False))

        return exists(subq)

    def _apply_sort(
        self,
        stmt,
        sort: RecordSort,
    ):
        """Apply sorting to query.

        Uses a scalar correlated subquery to fetch the sort value from
        record_values, then sorts by it.

        Args:
            stmt: SQLAlchemy select() statement
            sort: Sort specification

        Returns:
            Updated statement with ORDER BY clause
        """
        if not sort.property_id:
            return stmt

        # Scalar subquery to fetch property value for this record
        rv = aliased(RecordValue)
        sort_value_subq = (
            select(rv.value)
            .where(
                and_(
                    rv.record_id == Record.id,
                    rv.property_id == sort.property_id,
                )
            )
            .scalar_subquery()
        )

        # Try to cast to numeric for sorting, fall back to text
        sort_expr = case(
            (
                func.cast(sort_value_subq, float).isnot(None),
                func.cast(sort_value_subq, float),
            ),
            else_=literal(0),
        )

        if sort.direction.lower() == "asc":
            stmt = stmt.order_by(sort_expr.asc())
        else:
            stmt = stmt.order_by(sort_expr.desc())

        return stmt
