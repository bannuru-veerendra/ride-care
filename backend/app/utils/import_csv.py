"""CSV import helpers for fuel and service history uploads."""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from fastapi import HTTPException, UploadFile, status
from pydantic import ValidationError

from app.schemas.fuel_log import FuelLogCreate
from app.schemas.service_log import ServiceLogCreate

FUEL_REQUIRED_HEADERS = ("date", "odometer_km", "price_per_liter", "total_cost")

SERVICE_REQUIRED_HEADERS = ("date", "odometer_km", "total_cost", "services_done")

MAX_IMPORT_ROWS = 500
MAX_IMPORT_BYTES = 1_000_000
_READ_CHUNK = 64 * 1024
_ODOMETER_IN_DETAIL = re.compile(r"Odometer reading \((\d+(?:\.\d+)?)\)")


@dataclass
class CsvRowError:
    row: int
    message: str


@dataclass
class ParsedFuelRow:
    row: int
    payload: FuelLogCreate


@dataclass
class ParsedServiceRow:
    row: int
    payload: ServiceLogCreate


@dataclass
class FuelImportParseResult:
    rows: list[ParsedFuelRow] = field(default_factory=list)
    errors: list[CsvRowError] = field(default_factory=list)


@dataclass
class ServiceImportParseResult:
    rows: list[ParsedServiceRow] = field(default_factory=list)
    errors: list[CsvRowError] = field(default_factory=list)


def _normalize_headers(fieldnames: list[str] | None) -> list[str]:
    if not fieldnames:
        return []
    return [name.strip().lstrip("\ufeff") for name in fieldnames]


def _missing_headers(present: list[str], required: tuple[str, ...]) -> list[str]:
    present_set = set(present)
    return [name for name in required if name not in present_set]


def _cell(row: dict[str, str | None], key: str) -> str:
    value = row.get(key)
    if value is None:
        return ""
    return str(value).strip()


def _parse_date(value: str, label: str) -> date:
    if not value:
        raise ValueError(f"{label} is required")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{label} must be YYYY-MM-DD") from exc


def _parse_optional_date(value: str, label: str) -> date | None:
    if not value:
        return None
    return _parse_date(value, label)


def _parse_float(value: str, label: str) -> float:
    if not value:
        raise ValueError(f"{label} is required")
    try:
        return round(float(value), 2)
    except ValueError as exc:
        raise ValueError(f"{label} must be a number") from exc


def _parse_optional_float(value: str, label: str) -> float | None:
    if not value:
        return None
    return _parse_float(value, label)


def _split_services_done(value: str) -> list[str]:
    if not value:
        return []
    parts = [part.strip() for part in value.replace(",", ";").split(";")]
    return [part for part in parts if part]


def _format_validation_error(exc: ValidationError) -> str:
    messages: list[str] = []
    for err in exc.errors():
        msg = err.get("msg", "Invalid value")
        if isinstance(msg, str) and msg.startswith("Value error, "):
            msg = msg[len("Value error, ") :]
        messages.append(msg)
    return "; ".join(messages) if messages else "Invalid row"


async def read_csv_upload(
    file: UploadFile,
    *,
    max_bytes: int | None = None,
) -> bytes:
    """
    Read an upload in chunks and reject once it exceeds max_bytes.
    Avoids buffering a multi‑MB body before the size check.
    """
    limit = MAX_IMPORT_BYTES if max_bytes is None else max_bytes
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(_READ_CHUNK)
        if not chunk:
            break
        total += len(chunk)
        if total > limit:
            size_label = (
                f"{limit // 1000} KB" if limit >= 1000 else f"{limit} bytes"
            )
            raise ValueError(f"CSV file is too large (max {size_label})")
        chunks.append(chunk)
    return b"".join(chunks)


def decode_csv_upload(raw: bytes) -> str:
    """Decode uploaded CSV bytes (UTF-8 with optional BOM)."""
    if not raw.strip():
        raise ValueError("CSV file is empty")
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("CSV must be UTF-8 encoded") from exc


async def load_csv_text(
    file: UploadFile,
    *,
    max_bytes: int | None = None,
) -> str:
    """Read a capped upload and decode it as UTF-8 CSV text."""
    return decode_csv_upload(await read_csv_upload(file, max_bytes=max_bytes))


def parse_fuel_csv(text: str) -> FuelImportParseResult:
    """Parse export-compatible fuel CSV into create payloads."""
    result = FuelImportParseResult()
    reader = csv.DictReader(io.StringIO(text))
    headers = _normalize_headers(reader.fieldnames)
    missing = _missing_headers(headers, FUEL_REQUIRED_HEADERS)
    if missing:
        result.errors.append(
            CsvRowError(
                row=1,
                message=f"Missing required columns: {', '.join(missing)}",
            )
        )
        return result

    data_rows = 0
    for index, raw_row in enumerate(reader, start=2):
        if raw_row is None:
            continue
        # Skip completely blank lines
        if not any((_cell(raw_row, key) for key in headers)):
            continue
        data_rows += 1
        if data_rows > MAX_IMPORT_ROWS:
            result.errors.append(
                CsvRowError(
                    row=index,
                    message=f"Too many rows (max {MAX_IMPORT_ROWS})",
                )
            )
            break
        try:
            result.rows.append(
                ParsedFuelRow(
                    row=index,
                    payload=FuelLogCreate(
                        date=_parse_date(_cell(raw_row, "date"), "date"),
                        odometer=_parse_float(
                            _cell(raw_row, "odometer_km"), "odometer_km"
                        ),
                        total_cost=_parse_float(
                            _cell(raw_row, "total_cost"), "total_cost"
                        ),
                        price_per_liter=_parse_float(
                            _cell(raw_row, "price_per_liter"), "price_per_liter"
                        ),
                        notes=_cell(raw_row, "notes") or None,
                    ),
                )
            )
        except ValidationError as exc:
            result.errors.append(
                CsvRowError(row=index, message=_format_validation_error(exc))
            )
        except ValueError as exc:
            result.errors.append(CsvRowError(row=index, message=str(exc)))

    if data_rows == 0 and not result.errors:
        result.errors.append(CsvRowError(row=1, message="No data rows found"))
    return result


def parse_service_csv(text: str) -> ServiceImportParseResult:
    """Parse export-compatible service CSV into create payloads."""
    result = ServiceImportParseResult()
    reader = csv.DictReader(io.StringIO(text))
    headers = _normalize_headers(reader.fieldnames)
    missing = _missing_headers(headers, SERVICE_REQUIRED_HEADERS)
    if missing:
        result.errors.append(
            CsvRowError(
                row=1,
                message=f"Missing required columns: {', '.join(missing)}",
            )
        )
        return result

    data_rows = 0
    for index, raw_row in enumerate(reader, start=2):
        if raw_row is None:
            continue
        if not any((_cell(raw_row, key) for key in headers)):
            continue
        data_rows += 1
        if data_rows > MAX_IMPORT_ROWS:
            result.errors.append(
                CsvRowError(
                    row=index,
                    message=f"Too many rows (max {MAX_IMPORT_ROWS})",
                )
            )
            break
        try:
            services = _split_services_done(_cell(raw_row, "services_done"))
            result.rows.append(
                ParsedServiceRow(
                    row=index,
                    payload=ServiceLogCreate(
                        date=_parse_date(_cell(raw_row, "date"), "date"),
                        odometer=_parse_float(
                            _cell(raw_row, "odometer_km"), "odometer_km"
                        ),
                        total_cost=_parse_float(
                            _cell(raw_row, "total_cost"), "total_cost"
                        ),
                        services_done=services,
                        service_center=_cell(raw_row, "service_center") or None,
                        next_service_date=_parse_optional_date(
                            _cell(raw_row, "next_service_date"),
                            "next_service_date",
                        ),
                        next_service_odometer=_parse_optional_float(
                            _cell(raw_row, "next_service_odometer_km"),
                            "next_service_odometer_km",
                        ),
                        notes=_cell(raw_row, "notes") or None,
                    ),
                )
            )
        except ValidationError as exc:
            result.errors.append(
                CsvRowError(row=index, message=_format_validation_error(exc))
            )
        except ValueError as exc:
            result.errors.append(CsvRowError(row=index, message=str(exc)))

    if data_rows == 0 and not result.errors:
        result.errors.append(CsvRowError(row=1, message="No data rows found"))
    return result


def errors_to_detail(errors: list[CsvRowError]) -> dict[str, Any]:
    """Stable API error payload for failed imports."""
    return {
        "message": "CSV import failed",
        "errors": [{"row": err.row, "message": err.message} for err in errors],
    }


def raise_csv_import_errors(errors: list[CsvRowError]) -> None:
    """Raise HTTP 400 with the standard import error payload when errors exist."""
    if not errors:
        return
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=errors_to_detail(errors),
    )


async def require_csv_text(file: UploadFile) -> str:
    """Load CSV text or raise a structured 400 for empty/oversized/non-UTF8 files."""
    try:
        return await load_csv_text(file)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=errors_to_detail([CsvRowError(row=1, message=str(exc))]),
        ) from exc


def mileage_failure_detail(
    detail: str,
    ordered: list[ParsedFuelRow],
) -> dict[str, Any]:
    """Map a mileage-recalc error string onto the matching CSV row when possible."""
    row = 1
    match = _ODOMETER_IN_DETAIL.search(detail)
    if match:
        odometer = round(float(match.group(1)), 2)
        for item in ordered:
            if round(float(item.payload.odometer), 2) == odometer:
                row = item.row
                break
    return errors_to_detail([CsvRowError(row=row, message=detail)])
