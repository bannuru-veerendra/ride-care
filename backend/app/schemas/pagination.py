from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class CursorPage(BaseModel, Generic[T]):
    """Cursor-based paginated response"""

    items: list[T]
    next_cursor: str | None = None
    has_more: bool
    total: int
