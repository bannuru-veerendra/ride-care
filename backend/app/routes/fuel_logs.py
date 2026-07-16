import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.fuel_log import FuelLog
from app.models.user import User
from app.models.vehicle import Vehicle
from app.schemas.fuel_log import (
    FuelLogCreate,
    FuelLogResponse,
    FuelLogUpdate,
)
from app.utils.auth_dependency import get_current_user


router = APIRouter(prefix="/fuel_logs", tags=["fuel_logs"])


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
    db_vehicle = result.scalar_one_or_none()
    if not db_vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found",
        )
    return db_vehicle


async def get_owned_fuel_log(
    fuel_log_id: uuid.UUID,
    vehicle_id: uuid.UUID,
    current_user: User,
    db: AsyncSession,
) -> FuelLog:
    """Fetch a fuel log owned by the current user via vehicle ownership"""
    result = await db.execute(
        select(FuelLog)
        .join(Vehicle)
        .where(
            FuelLog.id == fuel_log_id,
            FuelLog.vehicle_id == vehicle_id,
            Vehicle.owner_id == current_user.id,
        )
    )
    db_fuel_log = result.scalar_one_or_none()
    if not db_fuel_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fuel log not found",
        )
    return db_fuel_log


async def recalculate_vehicle_fuel_mileage(
    db: AsyncSession,
    vehicle_id: uuid.UUID,
    vehicle: Vehicle,
) -> None:
    """Validate timeline and recalculate mileage for all fill-ups"""
    result = await db.execute(
        select(FuelLog)
        .where(FuelLog.vehicle_id == vehicle_id)
        .order_by(FuelLog.date.asc(), FuelLog.odometer.asc())
    )
    fuel_logs = list(result.scalars().all())

    previous_odometer = vehicle.current_odometer
    previous_label = (
        f"the vehicle's baseline odometer ({vehicle.current_odometer})"
    )

    for fuel_log in fuel_logs:
        if fuel_log.odometer <= previous_odometer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Odometer reading ({fuel_log.odometer}) must be greater than "
                    f"{previous_label}"
                ),
            )

        fuel_log.mileage = round(
            (fuel_log.odometer - previous_odometer) / fuel_log.liters
        )
        previous_odometer = fuel_log.odometer
        previous_label = f"the previous fill-up ({fuel_log.odometer})"


@router.post("/", response_model=FuelLogResponse, status_code=status.HTTP_201_CREATED)
async def create_fuel_log(
    fuel_log: FuelLogCreate,
    vehicle_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FuelLogResponse:
    """Create a new fuel log"""
    db_vehicle = await verify_vehicle_ownership(vehicle_id, current_user, db)
    db_fuel_log = FuelLog(
        **fuel_log.model_dump(),
        vehicle_id=vehicle_id,
        liters=fuel_log.total_cost / fuel_log.price_per_liter,
    )
    db.add(db_fuel_log)
    await db.flush()
    await recalculate_vehicle_fuel_mileage(db, vehicle_id, db_vehicle)
    await db.commit()
    await db.refresh(db_fuel_log)
    return db_fuel_log


@router.get("/", response_model=list[FuelLogResponse])
async def get_fuel_logs(
    vehicle_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[FuelLogResponse]:
    """Get all fuel logs for a vehicle"""
    await verify_vehicle_ownership(vehicle_id, current_user, db)
    result = await db.execute(
        select(FuelLog)
        .where(FuelLog.vehicle_id == vehicle_id)
        .order_by(FuelLog.date.desc(), FuelLog.odometer.desc())
    )
    return result.scalars().all()


@router.get("/{fuel_log_id}", response_model=FuelLogResponse)
async def get_fuel_log(
    fuel_log_id: uuid.UUID,
    vehicle_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FuelLogResponse:
    """Get a fuel log by ID"""
    return await get_owned_fuel_log(
        fuel_log_id,
        vehicle_id,
        current_user,
        db,
    )


@router.patch("/{fuel_log_id}", response_model=FuelLogResponse)
async def update_fuel_log(
    fuel_log_id: uuid.UUID,
    fuel_log: FuelLogUpdate,
    vehicle_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FuelLogResponse:
    """Update a fuel log by ID"""
    db_vehicle = await verify_vehicle_ownership(vehicle_id, current_user, db)
    db_fuel_log = await get_owned_fuel_log(
        fuel_log_id,
        vehicle_id,
        current_user,
        db,
    )

    updates = fuel_log.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(db_fuel_log, key, value)

    if "total_cost" in updates or "price_per_liter" in updates:
        db_fuel_log.liters = (
            db_fuel_log.total_cost / db_fuel_log.price_per_liter
        )

    if {"date", "odometer", "total_cost", "price_per_liter"} & updates.keys():
        await db.flush()
        await recalculate_vehicle_fuel_mileage(db, vehicle_id, db_vehicle)

    await db.commit()
    await db.refresh(db_fuel_log)
    return db_fuel_log


@router.delete("/{fuel_log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_fuel_log(
    fuel_log_id: uuid.UUID,
    vehicle_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a fuel log by ID"""
    db_vehicle = await verify_vehicle_ownership(vehicle_id, current_user, db)
    db_fuel_log = await get_owned_fuel_log(
        fuel_log_id,
        vehicle_id,
        current_user,
        db,
    )
    await db.delete(db_fuel_log)
    await db.flush()
    await recalculate_vehicle_fuel_mileage(db, vehicle_id, db_vehicle)
    await db.commit()
    return None
