import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import ValidationError
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.document import Document
from app.models.fuel_log import FuelLog
from app.models.service_log import ServiceLog
from app.models.user import User
from app.models.vehicle import Vehicle
from app.schemas.pagination import CursorPage
from app.schemas.vehicle import (
    VehicleAnalyticsResponse,
    VehicleCompareResponse,
    VehicleCreate,
    VehicleHealthResponse,
    VehicleResponse,
    VehicleSummaryResponse,
    VehicleUpdate,
)
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
    vehicle_health_key,
    vehicle_list_key,
    vehicle_summary_key,
)
from app.utils.dates import app_today
from app.utils.fuel_mileage import recalculate_vehicle_fuel_mileage
from app.utils.health import build_vehicle_health
from app.utils.numbers import round_2
from app.utils.odometer import get_live_odometer, get_live_odometers_map, get_min_log_odometer
from app.utils.pagination import paginate
from app.utils.redis_client import get_redis
from app.utils.storage import cleanup_document
from app.utils.vehicle_access import find_owned_vehicle
from app.utils.vehicle_analytics import build_analytics_response
from app.utils.vehicle_compare import build_compare_response
from app.utils.vehicle_summary import build_summary_payload, expiring_documents

router = APIRouter(prefix="/vehicles", tags=["vehicles"])

_NOT_FOUND = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Vehicle not found",
)


def build_vehicle_response(
    vehicle: Vehicle,
    live_odometer: float,
) -> VehicleResponse:
    """Build a vehicle response with baseline and live odometer."""
    return VehicleResponse(
        id=vehicle.id,
        owner_id=vehicle.owner_id,
        brand=vehicle.brand,
        vehicle_name=vehicle.vehicle_name,
        year=vehicle.year,
        registration_number=vehicle.registration_number,
        baseline_odometer=round_2(float(vehicle.current_odometer)),
        current_odometer=round_2(float(live_odometer)),
        reminders_muted=bool(vehicle.reminders_muted),
    )


async def to_vehicle_response(
    db: AsyncSession,
    vehicle: Vehicle,
) -> VehicleResponse:
    """Build a vehicle response with baseline and live odometer."""
    return build_vehicle_response(vehicle, await get_live_odometer(db, vehicle))


async def _invalidate_vehicle_caches(
    redis: Redis,
    *,
    user_id: uuid.UUID,
    vehicle_id: uuid.UUID | None = None,
) -> None:
    if vehicle_id is not None:
        vid = str(vehicle_id)
        await cache_delete(redis, vehicle_detail_key(vid))
        await cache_delete(
            redis,
            vehicle_summary_key(vid),
            vehicle_analytics_key(vid),
            vehicle_health_key(vid),
        )
    await cache_delete_pattern(redis, f"cache:vehicles:user:{user_id}*")


async def _cached_model(redis: Redis, cache_key: str, model):
    cached = await cache_get(redis, cache_key)
    if cached is CACHE_MISS:
        return None
    try:
        return model.model_validate(cached)
    except ValidationError:
        await cache_delete(redis, cache_key)
        return None


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

    await cache_delete_pattern(redis, f"cache:vehicles:user:{current_user.id}*")
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


@router.get("/compare", response_model=VehicleCompareResponse)
async def compare_vehicles(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> VehicleCompareResponse:
    """Side-by-side cost and mileage for every bike in the garage."""
    cache_key = vehicle_compare_key(str(current_user.id))
    cached = await _cached_model(redis, cache_key, VehicleCompareResponse)
    if cached is not None:
        return cached

    result = await db.execute(
        select(Vehicle)
        .where(Vehicle.owner_id == current_user.id)
        .order_by(Vehicle.created_at.desc())
    )
    vehicles = list(result.scalars().all())
    if not vehicles:
        payload = VehicleCompareResponse(items=[])
    else:
        payload = await build_compare_response(db, vehicles)
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
    db_vehicle = await find_owned_vehicle(db, vehicle_id, current_user.id)
    if db_vehicle is None:
        raise _NOT_FOUND

    cache_key = vehicle_summary_key(str(vehicle_id))
    cached = await _cached_model(redis, cache_key, VehicleSummaryResponse)
    if cached is not None:
        return cached

    payload = await build_summary_payload(db, db_vehicle)
    await cache_set(
        redis,
        cache_key,
        payload.model_dump(mode="json"),
        VEHICLE_CACHE_TTL,
    )
    return payload


@router.get("/{vehicle_id}/health", response_model=VehicleHealthResponse)
async def get_vehicle_health(
    vehicle_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> VehicleHealthResponse:
    """Ranked health signals + one recommended next action (no fake score)."""
    db_vehicle = await find_owned_vehicle(db, vehicle_id, current_user.id)
    if db_vehicle is None:
        raise _NOT_FOUND

    cache_key = vehicle_health_key(str(vehicle_id))
    cached = await _cached_model(redis, cache_key, VehicleHealthResponse)
    if cached is not None:
        return cached

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

    payload = build_vehicle_health(
        vehicle=db_vehicle,
        fuel_logs=fuel_logs,
        service_logs=service_logs,
        documents=await expiring_documents(db, vehicle_id),
        live_odometer=await get_live_odometer(db, db_vehicle),
        today=app_today(),
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
    """Return chart-ready analytics scanned across fuel and service logs."""
    db_vehicle = await find_owned_vehicle(db, vehicle_id, current_user.id)
    if db_vehicle is None:
        raise _NOT_FOUND

    cache_key = vehicle_analytics_key(str(vehicle_id))
    cached = await _cached_model(redis, cache_key, VehicleAnalyticsResponse)
    if cached is not None:
        return cached

    payload = await build_analytics_response(db, db_vehicle)
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
        if cached.get("owner_id") != str(current_user.id):
            raise _NOT_FOUND
        return cached

    db_vehicle = await find_owned_vehicle(db, vehicle_id, current_user.id)
    if not db_vehicle:
        raise _NOT_FOUND

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
    db_vehicle = await find_owned_vehicle(db, vehicle_id, current_user.id)
    if not db_vehicle:
        raise _NOT_FOUND

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

    await _invalidate_vehicle_caches(
        redis, user_id=current_user.id, vehicle_id=vehicle_id
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
    db_vehicle = await find_owned_vehicle(db, vehicle_id, current_user.id)
    if not db_vehicle:
        raise _NOT_FOUND

    storage_paths_result = await db.execute(
        select(Document.storage_path).where(Document.vehicle_id == vehicle_id)
    )
    storage_paths = list(storage_paths_result.scalars().all())

    await db.delete(db_vehicle)
    await db.commit()

    for storage_path in storage_paths:
        await cleanup_document(storage_path)

    await _invalidate_vehicle_caches(
        redis, user_id=current_user.id, vehicle_id=vehicle_id
    )
    return None
