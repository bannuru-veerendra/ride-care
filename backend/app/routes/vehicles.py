import uuid
from calendar import monthrange
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import ValidationError
from redis.asyncio import Redis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.document import Document
from app.models.fuel_log import FuelLog
from app.models.service_log import ServiceLog
from app.models.user import User
from app.models.vehicle import Vehicle
from app.schemas.pagination import CursorPage
from app.schemas.vehicle import (
    MileageTrendPoint,
    MonthlySpendPoint,
    VehicleAnalyticsResponse,
    VehicleCompareItem,
    VehicleCompareResponse,
    VehicleCreate,
    VehicleResponse,
    VehicleSummaryResponse,
    VehicleUpdate,
)
from app.utils.analytics import cost_per_km, km_driven, round_money
from app.utils.auth_dependency import get_current_user
from app.utils.cache import (
    CACHE_MISS,
    VEHICLE_CACHE_TTL,
    cache_delete,
    cache_delete_pattern,
    cache_get,
    cache_set,
    vehicle_analytics_key,
    vehicle_compare_key,
    vehicle_detail_key,
    vehicle_list_key,
    vehicle_summary_key,
)
from app.utils.dates import app_today
from app.utils.fuel_mileage import recalculate_vehicle_fuel_mileage
from app.utils.pagination import paginate
from app.utils.redis_client import get_redis
from app.utils.reminders import build_document_reminders, build_service_reminder
from app.utils.storage import cleanup_document

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


def _month_bounds(ref: date) -> tuple[date, date]:
    """Inclusive start/end dates for the calendar month of ref."""
    start = date(ref.year, ref.month, 1)
    end = date(ref.year, ref.month, monthrange(ref.year, ref.month)[1])
    return start, end


def _shift_month(ref: date, months: int) -> date:
    """Return the first day of the month offset by months from ref."""
    year = ref.year + (ref.month - 1 + months) // 12
    month = (ref.month - 1 + months) % 12 + 1
    return date(year, month, 1)


def _round_mileage(value: float | None) -> float | None:
    if value is None:
        return None
    return round(float(value), 1)


async def get_live_odometer(
    db: AsyncSession,
    vehicle: Vehicle,
) -> int:
    """Return the highest known odometer for a vehicle"""
    live_odometers = await get_live_odometers_map(db, [vehicle])
    return live_odometers[vehicle.id]


async def get_live_odometers_map(
    db: AsyncSession,
    vehicles: list[Vehicle],
) -> dict[uuid.UUID, int]:
    """Return live odometer for each vehicle in one round-trip."""
    if not vehicles:
        return {}

    vehicle_ids = [vehicle.id for vehicle in vehicles]
    baselines = {vehicle.id: vehicle.current_odometer for vehicle in vehicles}
    log_max_by_vehicle: dict[uuid.UUID, int] = {}

    fuel_max = (
        select(
            FuelLog.vehicle_id.label("vehicle_id"),
            func.max(FuelLog.odometer).label("odometer"),
        )
        .where(FuelLog.vehicle_id.in_(vehicle_ids))
        .group_by(FuelLog.vehicle_id)
    )
    service_max = (
        select(
            ServiceLog.vehicle_id.label("vehicle_id"),
            func.max(ServiceLog.odometer).label("odometer"),
        )
        .where(ServiceLog.vehicle_id.in_(vehicle_ids))
        .group_by(ServiceLog.vehicle_id)
    )
    log_max = fuel_max.union_all(service_max).subquery()
    result = await db.execute(
        select(log_max.c.vehicle_id, func.max(log_max.c.odometer)).group_by(
            log_max.c.vehicle_id
        )
    )
    for vehicle_id, odometer in result.all():
        log_max_by_vehicle[vehicle_id] = int(odometer or 0)

    return {
        vehicle_id: max(
            baselines[vehicle_id],
            log_max_by_vehicle.get(vehicle_id) or 0,
        )
        for vehicle_id in vehicle_ids
    }


def _average(values: list[float]) -> float | None:
    if not values:
        return None
    return _round_mileage(sum(values) / len(values))


async def _expiring_documents(
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


async def get_min_log_odometer(
    db: AsyncSession,
    vehicle_id: uuid.UUID,
) -> int | None:
    """Return the lowest fuel/service odometer for a vehicle, if any"""
    fuel_result = await db.execute(
        select(func.min(FuelLog.odometer)).where(
            FuelLog.vehicle_id == vehicle_id
        )
    )
    service_result = await db.execute(
        select(func.min(ServiceLog.odometer)).where(
            ServiceLog.vehicle_id == vehicle_id
        )
    )
    fuel_min = fuel_result.scalar_one_or_none()
    service_min = service_result.scalar_one_or_none()
    candidates = [value for value in (fuel_min, service_min) if value is not None]
    if not candidates:
        return None
    return min(candidates)


def build_vehicle_response(
    vehicle: Vehicle,
    live_odometer: int,
) -> VehicleResponse:
    """Build a vehicle response with baseline and live odometer"""
    return VehicleResponse(
        id=vehicle.id,
        owner_id=vehicle.owner_id,
        brand=vehicle.brand,
        vehicle_name=vehicle.vehicle_name,
        year=vehicle.year,
        registration_number=vehicle.registration_number,
        baseline_odometer=vehicle.current_odometer,
        current_odometer=live_odometer,
    )


async def to_vehicle_response(
    db: AsyncSession,
    vehicle: Vehicle,
) -> VehicleResponse:
    """Build a vehicle response with baseline and live odometer"""
    return build_vehicle_response(
        vehicle,
        await get_live_odometer(db, vehicle),
    )


async def _owned_vehicle(
    db: AsyncSession,
    vehicle_id: uuid.UUID,
    owner_id: uuid.UUID,
) -> Vehicle | None:
    result = await db.execute(
        select(Vehicle).where(
            Vehicle.id == vehicle_id,
            Vehicle.owner_id == owner_id,
        )
    )
    return result.scalar_one_or_none()


async def _fetch_vehicle_list(
    db: AsyncSession,
    redis: Redis,
    current_user: User,
    cursor: str | None = None,
    size: int = 100,
) -> CursorPage[VehicleResponse]:
    """Cached garage page."""
    cache_key = vehicle_list_key(str(current_user.id))
    if cursor or size != 20:
        cache_key = f"{cache_key}:{cursor}:{size}"

    cached = await cache_get(redis, cache_key)
    if cached is not CACHE_MISS:
        return CursorPage[VehicleResponse].model_validate(cached)

    try:
        page = await paginate(
            db,
            Vehicle,
            filter_clause=Vehicle.owner_id == current_user.id,
            order_by_column=Vehicle.created_at,
            cursor_column=Vehicle.created_at,
            tiebreaker_column=Vehicle.id,
            cursor=cursor,
            size=size,
            descending=True,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    live_odometers = await get_live_odometers_map(db, page.items)
    result = CursorPage(
        items=[
            build_vehicle_response(vehicle, live_odometers[vehicle.id])
            for vehicle in page.items
        ],
        next_cursor=page.next_cursor,
        has_more=page.has_more,
        total=page.total,
    )
    await cache_set(redis, cache_key, result.model_dump(mode="json"), VEHICLE_CACHE_TTL)
    return result


async def _build_summary_payload(
    db: AsyncSession,
    db_vehicle: Vehicle,
) -> VehicleSummaryResponse:
    """One fuel scan + one service scan + documents. Same connection, fewer round-trips."""
    vehicle_id = db_vehicle.id
    today = app_today()
    this_start, this_end = _month_bounds(today)
    last_start, last_end = _month_bounds(_shift_month(today, -1))

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

    documents = await _expiring_documents(db, vehicle_id)

    fuel_max = max((log.odometer for log in fuel_logs), default=0)
    service_max = max((log.odometer for log in service_logs), default=0)
    live_odometer = max(int(db_vehicle.current_odometer), fuel_max, service_max)

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
        mileage = _average(by_month[month_key])
        if mileage is not None:
            filled_months.append((month_key.strftime("%b"), mileage))
    recent_filled = filled_months[0] if len(filled_months) >= 1 else None
    prior_filled = filled_months[1] if len(filled_months) >= 2 else None

    next_service = next(
        (
            log
            for log in service_logs
            if log.next_service_date is not None
            or log.next_service_odometer is not None
        ),
        None,
    )

    return VehicleSummaryResponse(
        vehicle_id=vehicle_id,
        fuel_log_count=len(fuel_logs),
        average_mileage=_average(all_mileages),
        this_month_spend=this_month_spend,
        last_month_spend=last_month_spend,
        this_month_mileage=_average(this_mileages),
        last_month_mileage=_average(last_mileages),
        recent_filled_month_mileage=recent_filled[1] if recent_filled else None,
        prior_filled_month_mileage=prior_filled[1] if prior_filled else None,
        recent_filled_month_label=recent_filled[0] if recent_filled else None,
        prior_filled_month_label=prior_filled[0] if prior_filled else None,
        recent_fuel_logs=fuel_logs[:3],
        next_service=next_service,
        service_reminder=build_service_reminder(
            next_service,
            today=today,
            live_odometer=live_odometer,
        ),
        document_reminders=build_document_reminders(documents, today=today),
    )


async def _fetch_vehicle_summary(
    db: AsyncSession,
    redis: Redis,
    current_user: User,
    vehicle_id: uuid.UUID,
) -> VehicleSummaryResponse | None:
    db_vehicle = await _owned_vehicle(db, vehicle_id, current_user.id)
    if db_vehicle is None:
        return None

    cache_key = vehicle_summary_key(str(vehicle_id))
    cached = await cache_get(redis, cache_key)
    if cached is not CACHE_MISS:
        try:
            return VehicleSummaryResponse.model_validate(cached)
        except ValidationError:
            await cache_delete(redis, cache_key)

    payload = await _build_summary_payload(db, db_vehicle)
    await cache_set(
        redis,
        cache_key,
        payload.model_dump(mode="json"),
        VEHICLE_CACHE_TTL,
    )
    return payload


@router.post("/", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
async def create_vehicle(
    vehicle: VehicleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> VehicleResponse:
    """Create a new vehicle. Invalidates vehicle list cache."""
    result = await db.execute(
        select(Vehicle).where(
            Vehicle.registration_number == vehicle.registration_number
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vehicle with this registration number already exists",
        )

    payload = vehicle.model_dump()
    baseline_odometer = payload.pop("baseline_odometer")
    db_vehicle = Vehicle(
        **payload,
        current_odometer=baseline_odometer,
        owner_id=current_user.id,
    )
    db.add(db_vehicle)
    await db.commit()
    await db.refresh(db_vehicle)

    # Invalidate list cache — new vehicle must appear immediately
    await cache_delete_pattern(
        redis, f"cache:vehicles:user:{current_user.id}*"
    )
    return await to_vehicle_response(db, db_vehicle)


@router.get("/", response_model=CursorPage[VehicleResponse])
async def get_vehicles(
    cursor: str | None = Query(None),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> CursorPage[VehicleResponse]:
    """
    Get paginated vehicles for the current user.
    Cached per user for 5 minutes.
    Cache invalidated on any vehicle create/update/delete.
    """
    return await _fetch_vehicle_list(db, redis, current_user, cursor, size)


@router.get("/compare", response_model=VehicleCompareResponse)
async def compare_vehicles(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> VehicleCompareResponse:
    """Side-by-side cost and mileage for every bike in the garage."""
    cache_key = vehicle_compare_key(str(current_user.id))
    cached = await cache_get(redis, cache_key)
    if cached is not CACHE_MISS:
        try:
            return VehicleCompareResponse.model_validate(cached)
        except ValidationError:
            await cache_delete(redis, cache_key)

    result = await db.execute(
        select(Vehicle)
        .where(Vehicle.owner_id == current_user.id)
        .order_by(Vehicle.created_at.desc())
    )
    vehicles = list(result.scalars().all())
    if not vehicles:
        payload = VehicleCompareResponse(items=[])
        await cache_set(
            redis, cache_key, payload.model_dump(mode="json"), VEHICLE_CACHE_TTL
        )
        return payload

    live_odometers = await get_live_odometers_map(db, vehicles)
    vehicle_ids = [vehicle.id for vehicle in vehicles]

    fuel_result = await db.execute(
        select(
            FuelLog.vehicle_id,
            func.count().label("fill_ups"),
            func.coalesce(func.sum(FuelLog.total_cost), 0.0).label("fuel_spend"),
            func.avg(FuelLog.mileage).label("avg_mileage"),
        )
        .where(FuelLog.vehicle_id.in_(vehicle_ids))
        .group_by(FuelLog.vehicle_id)
    )
    fuel_by_vehicle = {row.vehicle_id: row for row in fuel_result.all()}

    service_result = await db.execute(
        select(
            ServiceLog.vehicle_id,
            func.count().label("service_count"),
            func.coalesce(func.sum(ServiceLog.total_cost), 0.0).label(
                "service_spend"
            ),
        )
        .where(ServiceLog.vehicle_id.in_(vehicle_ids))
        .group_by(ServiceLog.vehicle_id)
    )
    service_by_vehicle = {row.vehicle_id: row for row in service_result.all()}

    items: list[VehicleCompareItem] = []
    for vehicle in vehicles:
        fuel_row = fuel_by_vehicle.get(vehicle.id)
        service_row = service_by_vehicle.get(vehicle.id)
        fuel_spend = round_money(fuel_row.fuel_spend) if fuel_row else 0.0
        service_spend = (
            round_money(service_row.service_spend) if service_row else 0.0
        )
        combined = round_money(fuel_spend + service_spend)
        kilometers = km_driven(
            vehicle.current_odometer, live_odometers[vehicle.id]
        )
        items.append(
            VehicleCompareItem(
                vehicle_id=vehicle.id,
                brand=vehicle.brand,
                vehicle_name=vehicle.vehicle_name,
                year=vehicle.year,
                current_odometer=live_odometers[vehicle.id],
                km_driven=kilometers,
                avg_mileage=_round_mileage(
                    fuel_row.avg_mileage if fuel_row else None
                ),
                fuel_spend=fuel_spend,
                service_spend=service_spend,
                combined_spend=combined,
                cost_per_km=cost_per_km(combined, kilometers),
                fill_up_count=int(fuel_row.fill_ups) if fuel_row else 0,
                service_count=(
                    int(service_row.service_count) if service_row else 0
                ),
            )
        )

    payload = VehicleCompareResponse(items=items)
    await cache_set(
        redis, cache_key, payload.model_dump(mode="json"), VEHICLE_CACHE_TTL
    )
    return payload


@router.get("/{vehicle_id}/summary", response_model=VehicleSummaryResponse)
async def get_vehicle_summary(
    vehicle_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> VehicleSummaryResponse:
    """Return dashboard aggregations scanned across all fuel/service logs."""
    payload = await _fetch_vehicle_summary(db, redis, current_user, vehicle_id)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found",
        )
    return payload


@router.get("/{vehicle_id}/analytics", response_model=VehicleAnalyticsResponse)
async def get_vehicle_analytics(
    vehicle_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> VehicleAnalyticsResponse:
    """Return chart-ready analytics scanned across fuel and service logs."""
    result = await db.execute(
        select(Vehicle).where(
            Vehicle.id == vehicle_id,
            Vehicle.owner_id == current_user.id,
        )
    )
    db_vehicle = result.scalar_one_or_none()
    if db_vehicle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found",
        )

    cache_key = vehicle_analytics_key(str(vehicle_id))
    cached = await cache_get(redis, cache_key)
    if cached is not CACHE_MISS:
        try:
            return VehicleAnalyticsResponse.model_validate(cached)
        except ValidationError:
            await cache_delete(redis, cache_key)

    totals_result = await db.execute(
        select(
            func.count().label("total_fill_ups"),
            func.coalesce(func.sum(FuelLog.total_cost), 0.0).label("total_spend"),
            func.coalesce(func.sum(FuelLog.liters), 0.0).label("total_liters"),
        ).where(FuelLog.vehicle_id == vehicle_id)
    )
    totals = totals_result.one()

    mileage_stats_result = await db.execute(
        select(
            func.avg(FuelLog.mileage),
            func.max(FuelLog.mileage),
            func.min(FuelLog.mileage),
        ).where(
            FuelLog.vehicle_id == vehicle_id,
            FuelLog.mileage.isnot(None),
        )
    )
    avg_raw, best_raw, worst_raw = mileage_stats_result.one()

    trend_result = await db.execute(
        select(FuelLog)
        .where(
            FuelLog.vehicle_id == vehicle_id,
            FuelLog.mileage.isnot(None),
        )
        .order_by(FuelLog.date.desc(), FuelLog.odometer.desc())
        .limit(10)
    )
    trend_logs = list(reversed(list(trend_result.scalars().all())))
    mileage_trend = [
        MileageTrendPoint(
            date=log.date,
            date_label=log.date.strftime("%d %b"),
            mileage=_round_mileage(log.mileage) or 0.0,
            odometer=log.odometer,
        )
        for log in trend_logs
    ]

    today = app_today()
    monthly_spend: list[MonthlySpendPoint] = []
    for i in range(5, -1, -1):
        month_ref = _shift_month(today, -i)
        start, end = _month_bounds(month_ref)
        month_result = await db.execute(
            select(
                func.coalesce(func.sum(FuelLog.total_cost), 0.0),
                func.coalesce(func.sum(FuelLog.liters), 0.0),
            ).where(
                FuelLog.vehicle_id == vehicle_id,
                FuelLog.date >= start,
                FuelLog.date <= end,
            )
        )
        spend, liters = month_result.one()
        monthly_spend.append(
            MonthlySpendPoint(
                month=month_ref.strftime("%b"),
                year_month=month_ref.strftime("%Y-%m"),
                spend=float(spend),
                liters=round(float(liters), 2),
            )
        )

    service_totals_result = await db.execute(
        select(
            func.count().label("service_count"),
            func.coalesce(func.sum(ServiceLog.total_cost), 0.0).label(
                "service_spend"
            ),
        ).where(ServiceLog.vehicle_id == vehicle_id)
    )
    service_totals = service_totals_result.one()
    fuel_spend = round_money(totals.total_spend)
    service_spend = round_money(service_totals.service_spend)
    combined_spend = round_money(fuel_spend + service_spend)
    live_odometer = await get_live_odometer(db, db_vehicle)
    kilometers = km_driven(db_vehicle.current_odometer, live_odometer)

    payload = VehicleAnalyticsResponse(
        vehicle_id=vehicle_id,
        total_spend=fuel_spend,
        total_liters=round(float(totals.total_liters), 2),
        avg_mileage=_round_mileage(avg_raw),
        best_mileage=_round_mileage(best_raw),
        worst_mileage=_round_mileage(worst_raw),
        total_fill_ups=int(totals.total_fill_ups),
        mileage_trend=mileage_trend,
        monthly_spend=monthly_spend,
        service_spend=service_spend,
        service_count=int(service_totals.service_count),
        combined_spend=combined_spend,
        km_driven=kilometers,
        cost_per_km=cost_per_km(combined_spend, kilometers),
        fuel_cost_per_km=cost_per_km(fuel_spend, kilometers),
        service_cost_per_km=cost_per_km(service_spend, kilometers),
    )
    await cache_set(
        redis,
        cache_key,
        payload.model_dump(mode="json"),
        VEHICLE_CACHE_TTL,
    )
    return payload


@router.get("/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(
    vehicle_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> VehicleResponse:
    """
    Get a single vehicle by ID.
    Cached per vehicle for 5 minutes.
    """
    cache_key = vehicle_detail_key(str(vehicle_id))
    cached = await cache_get(redis, cache_key)
    if cached is not CACHE_MISS:
        # Verify ownership even on cache hit
        if cached.get("owner_id") != str(current_user.id):
            raise HTTPException(status_code=404, detail="Vehicle not found")
        return cached

    result = await db.execute(
        select(Vehicle).where(
            Vehicle.id == vehicle_id,
            Vehicle.owner_id == current_user.id,
        )
    )
    db_vehicle = result.scalar_one_or_none()
    if not db_vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found",
        )

    vehicle_response = await to_vehicle_response(db, db_vehicle)
    await cache_set(
        redis,
        cache_key,
        vehicle_response.model_dump(mode="json"),
        VEHICLE_CACHE_TTL,
    )
    return vehicle_response


@router.patch("/{vehicle_id}", response_model=VehicleResponse)
async def update_vehicle(
    vehicle_id: uuid.UUID,
    vehicle: VehicleUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> VehicleResponse:
    """Update a vehicle. Invalidates vehicle list and detail cache."""
    result = await db.execute(
        select(Vehicle).where(
            Vehicle.id == vehicle_id,
            Vehicle.owner_id == current_user.id,
        )
    )
    db_vehicle = result.scalar_one_or_none()
    if not db_vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found",
        )

    updates = vehicle.model_dump(exclude_unset=True)
    if "registration_number" in updates:
        existing = await db.execute(
            select(Vehicle).where(
                Vehicle.registration_number == updates["registration_number"],
                Vehicle.id != vehicle_id,
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Vehicle with this registration number already exists",
            )

    baseline_changed = False
    if "baseline_odometer" in updates:
        baseline_odometer = updates.pop("baseline_odometer")
        min_log_odometer = await get_min_log_odometer(db, vehicle_id)
        if min_log_odometer is not None and baseline_odometer >= min_log_odometer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Baseline odometer ({baseline_odometer}) must be less than "
                    f"the earliest fuel or service reading ({min_log_odometer})"
                ),
            )
        db_vehicle.current_odometer = baseline_odometer
        baseline_changed = True

    for key, value in updates.items():
        setattr(db_vehicle, key, value)

    if baseline_changed:
        await db.flush()
        await recalculate_vehicle_fuel_mileage(db, vehicle_id, db_vehicle)

    await db.commit()
    await db.refresh(db_vehicle)

    # Invalidate both list and detail cache
    await cache_delete(redis, vehicle_detail_key(str(vehicle_id)))
    await cache_delete(
        redis,
        vehicle_summary_key(str(vehicle_id)),
        vehicle_analytics_key(str(vehicle_id)),
    )
    await cache_delete_pattern(
        redis, f"cache:vehicles:user:{current_user.id}*"
    )
    return await to_vehicle_response(db, db_vehicle)


@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vehicle(
    vehicle_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> None:
    """Delete a vehicle. Invalidates all related caches."""
    result = await db.execute(
        select(Vehicle).where(
            Vehicle.id == vehicle_id,
            Vehicle.owner_id == current_user.id,
        )
    )
    db_vehicle = result.scalar_one_or_none()
    if not db_vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found",
        )

    storage_paths_result = await db.execute(
        select(Document.storage_path).where(Document.vehicle_id == vehicle_id)
    )
    storage_paths = list(storage_paths_result.scalars().all())

    await db.delete(db_vehicle)
    await db.commit()

    for storage_path in storage_paths:
        await cleanup_document(storage_path)

    # Invalidate caches
    await cache_delete(redis, vehicle_detail_key(str(vehicle_id)))
    await cache_delete(
        redis,
        vehicle_summary_key(str(vehicle_id)),
        vehicle_analytics_key(str(vehicle_id)),
    )
    await cache_delete_pattern(
        redis, f"cache:vehicles:user:{current_user.id}*"
    )
    return None
