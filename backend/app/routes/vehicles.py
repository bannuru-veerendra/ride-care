import uuid
from calendar import monthrange
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from redis.asyncio import Redis
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.fuel_log import FuelLog
from app.models.service_log import ServiceLog
from app.models.user import User
from app.models.vehicle import Vehicle
from app.schemas.pagination import CursorPage
from app.schemas.vehicle import (
    MileageTrendPoint,
    MonthlySpendPoint,
    VehicleAnalyticsResponse,
    VehicleCreate,
    VehicleResponse,
    VehicleSummaryResponse,
    VehicleUpdate,
)
from app.utils.auth_dependency import get_current_user
from app.utils.cache import (
    VEHICLE_CACHE_TTL,
    cache_delete,
    cache_delete_pattern,
    cache_get,
    cache_set,
    next_service_key,
    vehicle_analytics_key,
    vehicle_detail_key,
    vehicle_list_key,
    vehicle_summary_key,
)
from app.utils.dates import app_today
from app.utils.pagination import paginate
from app.utils.redis_client import get_redis

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


async def _last_two_filled_month_mileages(
    db: AsyncSession,
    vehicle_id: uuid.UUID,
) -> list[tuple[str, float]]:
    """
    Return up to two (month_label, avg_mileage) pairs for the most recent
    calendar months that have fuel logs with mileage.
    Example: Aug empty, Jul+Jun filled → [("Jul", 47.1), ("Jun", 45.0)]
    """
    month_start = func.date_trunc("month", FuelLog.date)
    result = await db.execute(
        select(
            month_start.label("month_start"),
            func.avg(FuelLog.mileage).label("avg_mileage"),
        )
        .where(
            FuelLog.vehicle_id == vehicle_id,
            FuelLog.mileage.isnot(None),
        )
        .group_by(month_start)
        .order_by(month_start.desc())
        .limit(2)
    )
    rows = result.all()
    filled: list[tuple[str, float]] = []
    for row in rows:
        month_value = row.month_start
        if month_value is None or row.avg_mileage is None:
            continue
        # date_trunc may return datetime
        if hasattr(month_value, "date"):
            month_date = month_value.date()
        else:
            month_date = month_value
        label = month_date.strftime("%b")
        mileage = _round_mileage(row.avg_mileage)
        if mileage is not None:
            filled.append((label, mileage))
    return filled


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
    """Return live odometer for each vehicle"""
    if not vehicles:
        return {}

    vehicle_ids = [vehicle.id for vehicle in vehicles]
    baselines = {vehicle.id: vehicle.current_odometer for vehicle in vehicles}

    fuel_result = await db.execute(
        select(FuelLog.vehicle_id, func.max(FuelLog.odometer))
        .where(FuelLog.vehicle_id.in_(vehicle_ids))
        .group_by(FuelLog.vehicle_id)
    )
    service_result = await db.execute(
        select(ServiceLog.vehicle_id, func.max(ServiceLog.odometer))
        .where(ServiceLog.vehicle_id.in_(vehicle_ids))
        .group_by(ServiceLog.vehicle_id)
    )

    fuel_max_by_vehicle = dict(fuel_result.all())
    service_max_by_vehicle = dict(service_result.all())

    return {
        vehicle_id: max(
            baselines[vehicle_id],
            fuel_max_by_vehicle.get(vehicle_id) or 0,
            service_max_by_vehicle.get(vehicle_id) or 0,
        )
        for vehicle_id in vehicle_ids
    }


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
    cache_key = vehicle_list_key(str(current_user.id))
    # Include cursor and size in cache key so different
    # pages are cached independently
    if cursor or size != 20:
        cache_key = f"{cache_key}:{cursor}:{size}"

    cached = await cache_get(redis, cache_key)
    if cached is not None:
        return cached

    page = await paginate(
        db,
        Vehicle,
        filter_clause=Vehicle.owner_id == current_user.id,
        order_by_column=Vehicle.created_at,
        cursor_column=Vehicle.created_at,
        cursor=cursor,
        size=size,
        descending=True,
    )
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


@router.get("/{vehicle_id}/summary", response_model=VehicleSummaryResponse)
async def get_vehicle_summary(
    vehicle_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> VehicleSummaryResponse:
    """Return dashboard aggregations scanned across all fuel/service logs."""
    result = await db.execute(
        select(Vehicle).where(
            Vehicle.id == vehicle_id,
            Vehicle.owner_id == current_user.id,
        )
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found",
        )

    cache_key = vehicle_summary_key(str(vehicle_id))
    cached = await cache_get(redis, cache_key)
    if cached is not None:
        return cached

    today = app_today()
    this_start, this_end = _month_bounds(today)
    last_start, last_end = _month_bounds(_shift_month(today, -1))

    count_result = await db.execute(
        select(func.count())
        .select_from(FuelLog)
        .where(FuelLog.vehicle_id == vehicle_id)
    )
    fuel_log_count = int(count_result.scalar_one())

    avg_result = await db.execute(
        select(func.avg(FuelLog.mileage)).where(
            FuelLog.vehicle_id == vehicle_id,
            FuelLog.mileage.isnot(None),
        )
    )
    average_mileage = _round_mileage(avg_result.scalar_one_or_none())

    async def month_spend(start: date, end: date) -> float:
        spend_result = await db.execute(
            select(func.coalesce(func.sum(FuelLog.total_cost), 0.0)).where(
                FuelLog.vehicle_id == vehicle_id,
                FuelLog.date >= start,
                FuelLog.date <= end,
            )
        )
        return float(spend_result.scalar_one())

    async def month_mileage(start: date, end: date) -> float | None:
        mileage_result = await db.execute(
            select(func.avg(FuelLog.mileage)).where(
                FuelLog.vehicle_id == vehicle_id,
                FuelLog.date >= start,
                FuelLog.date <= end,
                FuelLog.mileage.isnot(None),
            )
        )
        return _round_mileage(mileage_result.scalar_one_or_none())

    recent_result = await db.execute(
        select(FuelLog)
        .where(FuelLog.vehicle_id == vehicle_id)
        .order_by(FuelLog.date.desc(), FuelLog.odometer.desc())
        .limit(3)
    )
    recent_fuel_logs = list(recent_result.scalars().all())

    next_service_result = await db.execute(
        select(ServiceLog)
        .where(
            ServiceLog.vehicle_id == vehicle_id,
            or_(
                ServiceLog.next_service_date.isnot(None),
                ServiceLog.next_service_odometer.isnot(None),
            ),
        )
        .order_by(ServiceLog.date.desc(), ServiceLog.odometer.desc())
        .limit(1)
    )
    next_service = next_service_result.scalar_one_or_none()

    filled_months = await _last_two_filled_month_mileages(db, vehicle_id)
    recent_filled = filled_months[0] if len(filled_months) >= 1 else None
    prior_filled = filled_months[1] if len(filled_months) >= 2 else None

    payload = VehicleSummaryResponse(
        vehicle_id=vehicle_id,
        fuel_log_count=fuel_log_count,
        average_mileage=average_mileage,
        this_month_spend=await month_spend(this_start, this_end),
        last_month_spend=await month_spend(last_start, last_end),
        this_month_mileage=await month_mileage(this_start, this_end),
        last_month_mileage=await month_mileage(last_start, last_end),
        recent_filled_month_mileage=recent_filled[1] if recent_filled else None,
        prior_filled_month_mileage=prior_filled[1] if prior_filled else None,
        recent_filled_month_label=recent_filled[0] if recent_filled else None,
        prior_filled_month_label=prior_filled[0] if prior_filled else None,
        recent_fuel_logs=recent_fuel_logs,
        next_service=next_service,
    )
    await cache_set(
        redis,
        cache_key,
        payload.model_dump(mode="json"),
        VEHICLE_CACHE_TTL,
    )
    return payload


@router.get("/{vehicle_id}/analytics", response_model=VehicleAnalyticsResponse)
async def get_vehicle_analytics(
    vehicle_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> VehicleAnalyticsResponse:
    """Return chart-ready analytics scanned across all fuel logs."""
    result = await db.execute(
        select(Vehicle).where(
            Vehicle.id == vehicle_id,
            Vehicle.owner_id == current_user.id,
        )
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found",
        )

    cache_key = vehicle_analytics_key(str(vehicle_id))
    cached = await cache_get(redis, cache_key)
    if cached is not None:
        return cached

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

    payload = VehicleAnalyticsResponse(
        vehicle_id=vehicle_id,
        total_spend=float(totals.total_spend),
        total_liters=round(float(totals.total_liters), 2),
        avg_mileage=_round_mileage(avg_raw),
        best_mileage=_round_mileage(best_raw),
        worst_mileage=_round_mileage(worst_raw),
        total_fill_ups=int(totals.total_fill_ups),
        mileage_trend=mileage_trend,
        monthly_spend=monthly_spend,
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
    if cached is not None:
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

    for key, value in updates.items():
        setattr(db_vehicle, key, value)

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

    await db.delete(db_vehicle)
    await db.commit()

    # Invalidate caches
    await cache_delete(redis, vehicle_detail_key(str(vehicle_id)))
    await cache_delete(redis, next_service_key(str(vehicle_id)))
    await cache_delete(
        redis,
        vehicle_summary_key(str(vehicle_id)),
        vehicle_analytics_key(str(vehicle_id)),
    )
    await cache_delete_pattern(
        redis, f"cache:vehicles:user:{current_user.id}*"
    )
    return None
