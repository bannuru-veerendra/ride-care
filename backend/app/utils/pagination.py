import base64
from datetime import date, datetime
from typing import Any, Type, TypeVar
from uuid import UUID

from sqlalchemy import Date, DateTime, and_, func, or_, select
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.sql.sqltypes import Uuid as SAUuid

from app.schemas.pagination import CursorPage

T = TypeVar("T")

_CURSOR_SEP = "|"


def encode_cursor(value: str) -> str:
    """Base64-encode a cursor value so it stays opaque to clients"""
    return base64.urlsafe_b64encode(value.encode()).decode()


def decode_cursor(cursor: str) -> str:
    """Decode a base64 cursor back to its raw value"""
    return base64.urlsafe_b64decode(cursor.encode()).decode()


def coerce_cursor_value(
    cursor_column: InstrumentedAttribute,
    raw_cursor: str,
) -> Any:
    """Cast a decoded cursor string to the column's Python type"""
    column_type = cursor_column.type

    if isinstance(column_type, DateTime):
        return datetime.fromisoformat(raw_cursor)
    if isinstance(column_type, Date):
        return date.fromisoformat(raw_cursor)
    if isinstance(column_type, (PGUUID, SAUuid)):
        return UUID(raw_cursor)
    return raw_cursor


def _serialize_cursor_part(value: Any) -> str:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def encode_composite_cursor(primary: Any, tiebreaker: Any) -> str:
    """Encode primary + tiebreaker so same-day (or same-timestamp) rows paginate safely."""
    return encode_cursor(
        f"{_serialize_cursor_part(primary)}{_CURSOR_SEP}{_serialize_cursor_part(tiebreaker)}"
    )


def decode_composite_cursor(cursor: str) -> tuple[str, str]:
    """Decode a composite cursor into (primary, tiebreaker) raw strings."""
    raw = decode_cursor(cursor)
    primary, sep, tiebreaker = raw.partition(_CURSOR_SEP)
    if not sep or not primary or not tiebreaker:
        raise ValueError("Invalid pagination cursor")
    return primary, tiebreaker


async def paginate(
    db: AsyncSession,
    model: Type[T],
    *,
    filter_clause,
    order_by_column: InstrumentedAttribute,
    cursor: str | None,
    size: int,
    cursor_column: InstrumentedAttribute,
    tiebreaker_column: InstrumentedAttribute,
    descending: bool = True,
) -> CursorPage[T]:
    """
    Return a cursor-paginated page for any SQLAlchemy model.

    Cursors are (order column, tiebreaker id) so rows that share the same
    date/timestamp are never skipped across page boundaries.
    """
    count_result = await db.execute(
        select(func.count()).select_from(model).where(filter_clause)
    )
    total = count_result.scalar_one()

    conditions = [filter_clause]

    if cursor:
        try:
            raw_primary, raw_tiebreaker = decode_composite_cursor(cursor)
            primary = coerce_cursor_value(cursor_column, raw_primary)
            tiebreaker = coerce_cursor_value(tiebreaker_column, raw_tiebreaker)
        except (ValueError, TypeError) as exc:
            raise ValueError("Invalid pagination cursor") from exc

        if descending:
            conditions.append(
                or_(
                    cursor_column < primary,
                    and_(cursor_column == primary, tiebreaker_column < tiebreaker),
                )
            )
        else:
            conditions.append(
                or_(
                    cursor_column > primary,
                    and_(cursor_column == primary, tiebreaker_column > tiebreaker),
                )
            )

    primary_order = order_by_column.desc() if descending else order_by_column.asc()
    tiebreaker_order = (
        tiebreaker_column.desc() if descending else tiebreaker_column.asc()
    )

    query = (
        select(model)
        .where(and_(*conditions))
        .order_by(primary_order, tiebreaker_order)
        .limit(size + 1)
    )

    result = await db.execute(query)
    items = list(result.scalars().all())

    has_more = len(items) > size
    if has_more:
        items = items[:size]

    next_cursor = None
    if has_more and items:
        last = items[-1]
        next_cursor = encode_composite_cursor(
            getattr(last, cursor_column.key),
            getattr(last, tiebreaker_column.key),
        )

    return CursorPage(
        items=items,
        next_cursor=next_cursor,
        has_more=has_more,
        total=total,
    )
