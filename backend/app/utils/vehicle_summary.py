"""Dashboard summary aggregation for one vehicle."""

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.fuel_log import FuelLog
from app.models.service_log import ServiceLog
from app.models.vehicle import Vehicle
from app.schemas.vehicle import (
    DocumentReminder,
    ServiceReminder,
    VehicleSummaryResponse,
)
from app.utils.dates import app_today
from app.utils.months import month_bounds, shift_month
from app.utils.numbers import round_2
from app.utils.reminders import (
    build_document_reminders,
    build_service_reminder,
    find_active_next_service,
)


def round_mileage(value: float | None) -> float | None:
    if value is None:
        return None
    return round_2(value)


def average(values: list[float]) -> float | None:
    if not values:
        return None
    return round_mileage(sum(values) / len(values))


async def expiring_documents(
    db: AsyncSession,
    vehicle_id: uuid.UUID,
) -> list[Document]:
    result = await db.execute(
        select(Document)
        .where(
            Document.vehicle_id == vehicle_id,
            Document.expiry_date.isnot(None),
        )
        .order_by(Document.expiry_date.asc())
    )
    return list(result.scalars().all())


async def build_summary_payload(
    db: AsyncSession,
    db_vehicle: Vehicle,
) -> VehicleSummaryResponse:
    """One fuel scan + one service scan + documents. Same connection, fewer round-trips."""
    vehicle_id = db_vehicle.id
    today = app_today()
    this_start, this_end = month_bounds(today)
    last_start, last_end = month_bounds(shift_month(today, -1))

    fuel_result = await db.execute(
        select(FuelLog)
        .where(FuelLog.vehicle_id == vehicle_id)
        .order_by(FuelLog.date.desc(), FuelLog.odometer.desc())
    )
    fuel_logs = list(fuel_result.scalars().all())

    service_result = await db.execute(
        select(ServiceLog)
        .where(ServiceLog.vehicle_id == vehicle_id)
        .order_by(ServiceLog.date.desc(), ServiceLog.odometer.desc())
    )
    service_logs = list(service_result.scalars().all())

    documents = await expiring_documents(db, vehicle_id)

    fuel_max = max((float(log.odometer) for log in fuel_logs), default=0.0)
    service_max = max((float(log.odometer) for log in service_logs), default=0.0)
    live_odometer = round_2(
        max(float(db_vehicle.current_odometer), fuel_max, service_max)
    )

    this_mileages: list[float] = []
    last_mileages: list[float] = []
    all_mileages: list[float] = []
    this_month_spend = 0.0
    last_month_spend = 0.0
    by_month: dict[date, list[float]] = {}
    for log in fuel_logs:
        if this_start <= log.date <= this_end:
            this_month_spend += float(log.total_cost)
        elif last_start <= log.date <= last_end:
            last_month_spend += float(log.total_cost)
        if log.mileage is None:
            continue
        mileage = float(log.mileage)
        all_mileages.append(mileage)
        month_key = date(log.date.year, log.date.month, 1)
        by_month.setdefault(month_key, []).append(mileage)
        if this_start <= log.date <= this_end:
            this_mileages.append(mileage)
        elif last_start <= log.date <= last_end:
            last_mileages.append(mileage)

    filled_months: list[tuple[str, float]] = []
    for month_key in sorted(by_month.keys(), reverse=True)[:2]:
        mileage = average(by_month[month_key])
        if mileage is not None:
            filled_months.append((month_key.strftime("%b"), mileage))
    recent_filled = filled_months[0] if len(filled_months) >= 1 else None
    prior_filled = filled_months[1] if len(filled_months) >= 2 else None

    next_service = find_active_next_service(service_logs)

    if db_vehicle.reminders_muted:
        # Quiet urgency for digests / in-app nags, but keep schedule facts for the UI.
        built = build_service_reminder(
            next_service,
            today=today,
            live_odometer=live_odometer,
        )
        service_reminder = ServiceReminder(
            status="none",
            next_service_date=built.next_service_date,
            next_service_odometer=built.next_service_odometer,
        )
        document_reminders: list[DocumentReminder] = []
    else:
        service_reminder = build_service_reminder(
            next_service,
            today=today,
            live_odometer=live_odometer,
        )
        document_reminders = build_document_reminders(documents, today=today)

    return VehicleSummaryResponse(
        vehicle_id=vehicle_id,
        fuel_log_count=len(fuel_logs),
        average_mileage=average(all_mileages),
        this_month_spend=this_month_spend,
        last_month_spend=last_month_spend,
        this_month_mileage=average(this_mileages),
        last_month_mileage=average(last_mileages),
        recent_filled_month_mileage=recent_filled[1] if recent_filled else None,
        prior_filled_month_mileage=prior_filled[1] if prior_filled else None,
        recent_filled_month_label=recent_filled[0] if recent_filled else None,
        prior_filled_month_label=prior_filled[0] if prior_filled else None,
        recent_fuel_logs=fuel_logs[:3],
        next_service=next_service,
        service_reminder=service_reminder,
        document_reminders=document_reminders,
    )
