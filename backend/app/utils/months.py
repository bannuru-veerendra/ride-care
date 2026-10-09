"""Calendar-month helpers for summary and analytics windows."""

from calendar import monthrange
from datetime import date


def month_bounds(ref: date) -> tuple[date, date]:
    """Inclusive start/end dates for the calendar month of ref."""
    start = date(ref.year, ref.month, 1)
    end = date(ref.year, ref.month, monthrange(ref.year, ref.month)[1])
    return start, end


def shift_month(ref: date, months: int) -> date:
    """Return the first day of the month offset by months from ref."""
    year = ref.year + (ref.month - 1 + months) // 12
    month = (ref.month - 1 + months) % 12 + 1
    return date(year, month, 1)
