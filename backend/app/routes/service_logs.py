import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.service_log import ServiceLog
from app.models.user import User
from app.models.vehicle import Vehicle
from app.schemas.service_log import ServiceLogCreate, ServiceLogResponse, ServiceLogUpdate
from app.utils.auth_dependency import get_current_user


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
    return db_service_log


@router.get("/", response_model=list[ServiceLogResponse])
async def get_service_logs(
    vehicle_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ServiceLogResponse]:
    """Get all service logs for a vehicle"""
    await verify_vehicle_ownership(vehicle_id, current_user, db)
    
    result = await db.execute(
        select(ServiceLog)
        .where(ServiceLog.vehicle_id == vehicle_id)
        .order_by(ServiceLog.date.desc())
    )
    return result.scalars().all()


@router.get("/next", response_model=ServiceLogResponse | None)
async def get_next_service_log(
    vehicle_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ServiceLogResponse | None:
    """Get the next service log for a vehicle"""
    await verify_vehicle_ownership(vehicle_id, current_user, db)
    result = await db.execute(
        select(ServiceLog)
        .where(
            ServiceLog.vehicle_id == vehicle_id,
            ServiceLog.next_service_date.isnot(None),
        )
        .order_by(ServiceLog.date.asc())
        .limit(1)
    )
    return result.scalar_one_or_none()


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
) -> ServiceLogResponse:
    """Update a service log by ID"""
    db_service_log = await get_owned_service_log(service_log_id, vehicle_id, current_user, db)
    
    updates = service_log.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(db_service_log, key, value)
    await db.commit()
    await db.refresh(db_service_log)
    return db_service_log
    

@router.delete("/{service_log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service_log(
    service_log_id: uuid.UUID,
    vehicle_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a service log by ID"""
    db_service_log = await get_owned_service_log(service_log_id, vehicle_id, current_user, db)
    await db.delete(db_service_log)
    await db.commit()
    return None