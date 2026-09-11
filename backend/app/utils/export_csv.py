"""CSV export helpers for fuel and service history downloads."""

from __future__ import annotations

import csv
import io
import re
from collections.abc import Iterable, Sequence
from typing import Any
from urllib.parse import quote

_UNSAFE_FILENAME = re.compile(r"[^\w\-]+", re.UNICODE)
_MULTI_DASH = re.compile(r"-{2,}")
_ASCII_FILENAME = re.compile(r"[^A-Za-z0-9._\-]+")


def csv_download_filename(kind: str, vehicle_name: str, fallback_id: str) -> str:
    """Build a safe download name like ridecare-fuel-shine-100.csv."""
    slug = _MULTI_DASH.sub(
        "-",
        _UNSAFE_FILENAME.sub("-", (vehicle_name or "").strip()),
    ).strip("-")
    if not slug:
        slug = str(fallback_id)
    return f"ridecare-{kind}-{slug}.csv"


def content_disposition_attachment(filename: str) -> str:
    """
    Build Content-Disposition with ASCII fallback + RFC 5987 UTF-8 filename*.
    """
    ascii_name = _ASCII_FILENAME.sub("-", filename).strip("-._") or "export.csv"
    return (
        f'attachment; filename="{ascii_name}"; '
        f"filename*=UTF-8''{quote(filename)}"
    )


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
