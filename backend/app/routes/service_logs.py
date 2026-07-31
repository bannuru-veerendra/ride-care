import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.service_log import ServiceLog
from app.models.user import User
from app.models.vehicle import Vehicle
from app.schemas.pagination import CursorPage
from app.schemas.service_log import ServiceLogCreate, ServiceLogResponse, ServiceLogUpdate
from app.utils.auth_dependency import get_current_user
from app.utils.cache import (
    NEXT_SERVICE_CACHE_TTL,
    cache_delete,
    cache_get,
    cache_set,
    next_service_key,
)
from app.utils.pagination import paginate
from app.utils.redis_client import get_redis


router = APIRouter(prefix="/service_logs", tags=["service_logs"])


async def verify_vehicle_ownership(
    vehicle_id: uuid.UUID,
    current_user: User,
    db: AsyncSession,
) -> Vehicle:
    """Verify that the current user owns the vehicle"""
    result = await db.execute(
        select(Vehicle).where(
            Vehicle.id == vehicle_id,
            Vehicle.owner_id == current_user.id,
        )
    )
    vehicle = result.scalar_one_or_none()
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found",
        )
    return vehicle


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


@router.post("/", response_model=ServiceLogResponse, status_code=status.HTTP_201_CREATED)
async def create_service_log(
    service_log: ServiceLogCreate,
    vehicle_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> ServiceLogResponse:
    """Create a new service log"""
    await verify_vehicle_ownership(vehicle_id, current_user, db)
    db_service_log = ServiceLog(
        **service_log.model_dump(),
        vehicle_id=vehicle_id,
    )
    db.add(db_service_log)
    await db.commit()
    await db.refresh(db_service_log)
    await cache_delete(redis, next_service_key(str(vehicle_id)))
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

    return await paginate(
        db,
        ServiceLog,
        filter_clause=ServiceLog.vehicle_id == vehicle_id,
        order_by_column=ServiceLog.date,
        cursor_column=ServiceLog.date,
        cursor=cursor,
        size=size,
        descending=True,
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
    if cached is not None:
        return cached

    result = await db.execute(
        select(ServiceLog)
        .where(
            ServiceLog.vehicle_id == vehicle_id,
            ServiceLog.next_service_date.isnot(None),
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
    db_service_log = await get_owned_service_log(
        service_log_id,
        vehicle_id,
        current_user,
        db,
    )

    updates = service_log.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(db_service_log, key, value)
    await db.commit()
    await db.refresh(db_service_log)
    await cache_delete(redis, next_service_key(str(vehicle_id)))
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
    db_service_log = await get_owned_service_log(
        service_log_id,
        vehicle_id,
        current_user,
        db,
    )
    await db.delete(db_service_log)
    await db.commit()
    await cache_delete(redis, next_service_key(str(vehicle_id)))
    return None
