import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from redis.asyncio import Redis
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.service_log import ServiceLog
from app.models.user import User
from app.models.vehicle import Vehicle
from app.schemas.pagination import CursorPage
from app.schemas.service_log import ServiceLogCreate, ServiceLogResponse, ServiceLogUpdate
from app.utils.auth_dependency import get_current_user
from app.utils.cache import (
    CACHE_MISS,
    NEXT_SERVICE_CACHE_TTL,
    cache_delete,
    cache_delete_pattern,
    cache_get,
    cache_set,
    next_service_key,
    vehicle_analytics_key,
    vehicle_detail_key,
    vehicle_summary_key,
)
from app.utils.export_csv import service_log_csv_rows
from app.utils.pagination import paginate
from app.utils.redis_client import get_redis
from app.utils.vehicle_access import verify_vehicle_ownership


router = APIRouter(prefix="/service_logs", tags=["service_logs"])


async def _invalidate_service_derived_caches(
    redis: Redis,
    vehicle_id: uuid.UUID,
    owner_id: uuid.UUID,
) -> None:
    """Drop caches that depend on service logs / live odometer."""
    await cache_delete(
        redis,
        next_service_key(str(vehicle_id)),
        vehicle_summary_key(str(vehicle_id)),
        vehicle_detail_key(str(vehicle_id)),
        vehicle_analytics_key(str(vehicle_id)),
    )
    await cache_delete_pattern(redis, f"cache:vehicles:user:{owner_id}*")


async def get_owned_service_log(
    service_log_id: uuid.UUID,
    vehicle_id: uuid.UUID,
    current_user: User,
    db: AsyncSession,
) -> ServiceLog:
    """Fetch a service log owned by the current user via vehicle ownership"""
    result = await db.execute(
        select(ServiceLog).join(Vehicle).where(
            ServiceLog.id == service_log_id,
            ServiceLog.vehicle_id == vehicle_id,
            Vehicle.owner_id == current_user.id,
        )
    )
    db_service_log = result.scalar_one_or_none()
    if not db_service_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service log not found",
        )
    return db_service_log


def _validate_next_service_odometer(
    odometer: int,
    next_service_odometer: int | None,
) -> None:
    if next_service_odometer is not None and next_service_odometer <= odometer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Next service odometer must be greater than the current odometer",
        )


def _validate_service_odometer_against_baseline(
    odometer: int,
    baseline_odometer: int,
) -> None:
    """Service readings feed live odometer — reject values below the vehicle baseline."""
    if odometer < baseline_odometer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Odometer reading ({odometer}) must be greater than or equal to "
                f"the vehicle's baseline odometer ({baseline_odometer})"
            ),
        )


@router.post("/", response_model=ServiceLogResponse, status_code=status.HTTP_201_CREATED)
async def create_service_log(
    service_log: ServiceLogCreate,
    vehicle_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> ServiceLogResponse:
    """Create a new service log"""
    db_vehicle = await verify_vehicle_ownership(vehicle_id, current_user, db)
    _validate_service_odometer_against_baseline(
        service_log.odometer,
        db_vehicle.current_odometer,
    )
    db_service_log = ServiceLog(
        **service_log.model_dump(),
        vehicle_id=vehicle_id,
    )
    db.add(db_service_log)
    await db.commit()
    await db.refresh(db_service_log)
    await _invalidate_service_derived_caches(redis, vehicle_id, db_vehicle.owner_id)
    return db_service_log


@router.get("/", response_model=CursorPage[ServiceLogResponse])
async def get_service_logs(
    vehicle_id: uuid.UUID,
    cursor: str | None = Query(None),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CursorPage[ServiceLogResponse]:
    """Get paginated service logs for a vehicle"""
    await verify_vehicle_ownership(vehicle_id, current_user, db)

    try:
        return await paginate(
            db,
            ServiceLog,
            filter_clause=ServiceLog.vehicle_id == vehicle_id,
            order_by_column=ServiceLog.date,
            cursor_column=ServiceLog.date,
            tiebreaker_column=ServiceLog.id,
            cursor=cursor,
            size=size,
            descending=True,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get("/export")
async def export_service_logs_csv(
    vehicle_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Download all service logs for a vehicle as CSV (newest first)."""
    await verify_vehicle_ownership(vehicle_id, current_user, db)
    result = await db.execute(
        select(ServiceLog)
        .where(ServiceLog.vehicle_id == vehicle_id)
        .order_by(ServiceLog.date.desc(), ServiceLog.id.desc())
    )
    logs = list(result.scalars().all())
    csv_body = service_log_csv_rows(logs)
    filename = f"ridecare-service-{vehicle_id}.csv"
    return Response(
        content=csv_body,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.get("/next", response_model=ServiceLogResponse | None)
async def get_next_service_log(
    vehicle_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> ServiceLogResponse | None:
    """
    Returns the most recent service log with next service info.
    Cached per vehicle for 5 minutes.
    """
    await verify_vehicle_ownership(vehicle_id, current_user, db)

    cache_key = next_service_key(str(vehicle_id))
    cached = await cache_get(redis, cache_key)
    if cached is not CACHE_MISS:
        return cached

    result = await db.execute(
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
    service_log = result.scalar_one_or_none()

    value = (
        ServiceLogResponse.model_validate(service_log).model_dump(mode="json")
        if service_log
        else None
    )
    await cache_set(redis, cache_key, value, NEXT_SERVICE_CACHE_TTL)
    return service_log


@router.get("/{service_log_id}", response_model=ServiceLogResponse)
async def get_service_log(
    service_log_id: uuid.UUID,
    vehicle_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ServiceLogResponse:
    """Get a service log by ID"""
    return await get_owned_service_log(
        service_log_id,
        vehicle_id,
        current_user,
        db,
    )


@router.patch("/{service_log_id}", response_model=ServiceLogResponse)
async def update_service_log(
    service_log_id: uuid.UUID,
    service_log: ServiceLogUpdate,
    vehicle_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> ServiceLogResponse:
    """Update a service log by ID"""
    db_vehicle = await verify_vehicle_ownership(vehicle_id, current_user, db)
    db_service_log = await get_owned_service_log(
        service_log_id,
        vehicle_id,
        current_user,
        db,
    )

    updates = service_log.model_dump(exclude_unset=True)
    merged_odometer = updates.get("odometer", db_service_log.odometer)
    merged_next = (
        updates["next_service_odometer"]
        if "next_service_odometer" in updates
        else db_service_log.next_service_odometer
    )
    _validate_service_odometer_against_baseline(
        merged_odometer,
        db_vehicle.current_odometer,
    )
    _validate_next_service_odometer(merged_odometer, merged_next)

    for key, value in updates.items():
        setattr(db_service_log, key, value)
    await db.commit()
    await db.refresh(db_service_log)
    await _invalidate_service_derived_caches(redis, vehicle_id, db_vehicle.owner_id)
    return db_service_log


@router.delete("/{service_log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service_log(
    service_log_id: uuid.UUID,
    vehicle_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> None:
    """Delete a service log by ID"""
    db_vehicle = await verify_vehicle_ownership(vehicle_id, current_user, db)
    db_service_log = await get_owned_service_log(
        service_log_id,
        vehicle_id,
        current_user,
        db,
    )
    await db.delete(db_service_log)
    await db.commit()
    await _invalidate_service_derived_caches(redis, vehicle_id, db_vehicle.owner_id)
    return None
