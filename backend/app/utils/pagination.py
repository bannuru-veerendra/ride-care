import base64
from datetime import date, datetime
from typing import Any, Type, TypeVar
from uuid import UUID

from sqlalchemy import Date, DateTime, and_, func, select
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.sql.sqltypes import Uuid as SAUuid

from app.schemas.pagination import CursorPage

T = TypeVar("T")


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


async def paginate(
    db: AsyncSession,
    model: Type[T],
    *,
    filter_clause,
    order_by_column: InstrumentedAttribute,
    cursor: str | None,
    size: int,
    cursor_column: InstrumentedAttribute,
    descending: bool = True,
) -> CursorPage[T]:
    """Return a cursor-paginated page for any SQLAlchemy model"""
    count_result = await db.execute(
        select(func.count()).select_from(model).where(filter_clause)
    )
    total = count_result.scalar_one()

    conditions = [filter_clause]

    if cursor:
        raw_cursor = coerce_cursor_value(cursor_column, decode_cursor(cursor))
        if descending:
            conditions.append(cursor_column < raw_cursor)
        else:
            conditions.append(cursor_column > raw_cursor)

    query = (
        select(model)
        .where(and_(*conditions))
        .order_by(
            order_by_column.desc() if descending else order_by_column.asc()
        )
        .limit(size + 1)
    )

    result = await db.execute(query)
    items = list(result.scalars().all())

    has_more = len(items) > size
    if has_more:
        items = items[:size]

    next_cursor = None
    if has_more and items:
        last_value = getattr(items[-1], cursor_column.key)
        if hasattr(last_value, "isoformat"):
            cursor_raw = last_value.isoformat()
        else:
            cursor_raw = str(last_value)
        next_cursor = encode_cursor(cursor_raw)

    return CursorPage(
        items=items,
        next_cursor=next_cursor,
        has_more=has_more,
        total=total,
    )
