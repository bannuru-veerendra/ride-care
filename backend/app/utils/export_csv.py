"""CSV export helpers for fuel and service history downloads."""

from __future__ import annotations

import csv
import io
from collections.abc import Iterable, Sequence
from typing import Any


def rows_to_csv(headers: Sequence[str], rows: Iterable[Sequence[Any]]) -> str:
    """Serialize header + data rows to a UTF-8 CSV string (Excel-friendly BOM)."""
    buffer = io.StringIO()
    # BOM helps Excel open UTF-8 correctly on Windows
    buffer.write("\ufeff")
    writer = csv.writer(buffer)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(["" if value is None else value for value in row])
    return buffer.getvalue()


def fuel_log_csv_rows(logs: Sequence[Any]) -> str:
    """Build CSV for fuel fill-ups (newest-first order preserved by caller)."""
    headers = (
        "date",
        "odometer_km",
        "liters",
        "price_per_liter",
        "total_cost",
        "mileage_km_per_l",
        "notes",
    )
    rows = (
        (
            log.date.isoformat() if log.date is not None else "",
            log.odometer,
            log.liters,
            log.price_per_liter,
            log.total_cost,
            log.mileage,
            log.notes or "",
        )
        for log in logs
    )
    return rows_to_csv(headers, rows)


def service_log_csv_rows(logs: Sequence[Any]) -> str:
    """Build CSV for service visits (newest-first order preserved by caller)."""
    headers = (
        "date",
        "odometer_km",
        "service_center",
        "total_cost",
        "services_done",
        "next_service_date",
        "next_service_odometer_km",
        "notes",
    )
    rows = (
        (
            log.date.isoformat() if log.date is not None else "",
            log.odometer,
            log.service_center or "",
            log.total_cost,
            "; ".join(log.services_done or []),
            (
                log.next_service_date.isoformat()
                if log.next_service_date is not None
                else ""
            ),
            log.next_service_odometer,
            log.notes or "",
        )
        for log in logs
    )
    return rows_to_csv(headers, rows)
