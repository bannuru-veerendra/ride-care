"""In-app reminder thresholds and status helpers (API-owned domain rules)."""

from __future__ import annotations

from datetime import date
from typing import Literal

from app.models.document import Document
from app.models.service_log import ServiceLog
from app.schemas.vehicle import DocumentReminder, ServiceReminder

SERVICE_SOON_DAYS = 14
SERVICE_SOON_KM = 500
DOCUMENT_SOON_DAYS = 30
DOCUMENT_REMINDER_LIMIT = 5

DocumentExpiryStatus = Literal["ok", "soon", "expired"]


def _visit_is_after(schedule: ServiceLog, visit: ServiceLog) -> bool:
    """True when visit is a later service record than the schedule's visit."""
    if visit.id == schedule.id:
        return False
    return (visit.date, visit.odometer) > (schedule.date, schedule.odometer)


def _schedule_fulfilled_by(schedule: ServiceLog, visit: ServiceLog) -> bool:
    """
    True when a later visit met every next-due target on the schedule log.

    Example: schedule says next service by 18 Aug — a visit on or after 18 Aug
    clears the date target. If both date and km are set, both must be met.
    """
    if not _visit_is_after(schedule, visit):
        return False

    date_ok = (
        schedule.next_service_date is None
        or visit.date >= schedule.next_service_date
    )
    odo_ok = (
        schedule.next_service_odometer is None
        or visit.odometer >= schedule.next_service_odometer
    )
    return date_ok and odo_ok


def find_active_next_service(service_logs: list[ServiceLog]) -> ServiceLog | None:
    """
    Newest visit that still has next-due fields and was not fulfilled by a
    later service log. service_logs should be ordered newest visit first.
    """
    for log in service_logs:
        if log.next_service_date is None and log.next_service_odometer is None:
            continue
        if any(_schedule_fulfilled_by(log, visit) for visit in service_logs):
            continue
        return log
    return None


def document_expiry_fields(
    expiry_date: date | None,
    *,
    today: date,
) -> tuple[int | None, DocumentExpiryStatus | None]:
    """Return (days_until, expiry_status) for a document expiry date."""
    if expiry_date is None:
        return None, None

    days_until = (expiry_date - today).days
    if days_until < 0:
        return days_until, "expired"
    if days_until <= DOCUMENT_SOON_DAYS:
        return days_until, "soon"
    return days_until, "ok"


def build_service_reminder(
    next_service: ServiceLog | None,
    *,
    today: date,
    live_odometer: int,
) -> ServiceReminder:
    """Compute next-service urgency from date and/or odometer targets."""
    if next_service is None:
        return ServiceReminder(status="none")

    next_date = next_service.next_service_date
    next_odo = next_service.next_service_odometer
    if next_date is None and next_odo is None:
        return ServiceReminder(status="none")

    days_until = (next_date - today).days if next_date is not None else None
    km_until = (next_odo - live_odometer) if next_odo is not None else None

    overdue = (days_until is not None and days_until < 0) or (
        km_until is not None and km_until < 0
    )
    soon = not overdue and (
        (days_until is not None and 0 <= days_until <= SERVICE_SOON_DAYS)
        or (km_until is not None and 0 <= km_until <= SERVICE_SOON_KM)
    )

    if overdue:
        status = "overdue"
    elif soon:
        status = "soon"
    else:
        status = "ok"

    return ServiceReminder(
        status=status,
        days_until=days_until,
        km_until=km_until,
        next_service_date=next_date,
        next_service_odometer=next_odo,
    )


def build_document_reminders(
    documents: list[Document],
    *,
    today: date,
) -> list[DocumentReminder]:
    """Return soon/expired document expiry reminders, soonest first."""
    reminders: list[DocumentReminder] = []
    for document in documents:
        days_until, status = document_expiry_fields(
            document.expiry_date, today=today
        )
        if status not in ("soon", "expired") or days_until is None:
            continue
        if document.expiry_date is None:
            continue

        doc_type = document.document_type
        type_value = doc_type.value if hasattr(doc_type, "value") else str(doc_type)
        reminders.append(
            DocumentReminder(
                id=document.id,
                document_type=type_value,
                expiry_date=document.expiry_date,
                days_until=days_until,
                status=status,
            )
        )
        if len(reminders) >= DOCUMENT_REMINDER_LIMIT:
            break
    return reminders
