import uuid
from datetime import date as dt_date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
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


async def get_previous_fuel_log(
    db: AsyncSession,
    vehicle_id: uuid.UUID,
    log_date: dt_date,
    odometer: int,
    exclude_id: uuid.UUID | None = None,
) -> FuelLog | None:
    """Find the chronologically prior fill-up for mileage calculation."""
    conditions = [
        FuelLog.vehicle_id == vehicle_id,
        or_(
            FuelLog.date < log_date,
            (FuelLog.date == log_date) & (FuelLog.odometer < odometer),
        ),
    ]
    if exclude_id is not None:
        conditions.append(FuelLog.id != exclude_id)

    result = await db.execute(
        select(FuelLog)
        .where(*conditions)
        .order_by(FuelLog.date.desc(), FuelLog.odometer.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


def resolve_previous_odometer(
    odometer: int,
    previous_fuel_log: FuelLog | None,
    vehicle: Vehicle,
) -> int | None:
    """Odometer reading to measure distance since last fill-up."""
    if previous_fuel_log is not None:
        return previous_fuel_log.odometer
    if (
        vehicle.current_odometer > 0
        and odometer > vehicle.current_odometer
    ):
        return vehicle.current_odometer
    return None


def calculate_mileage(
    odometer: int,
    liters: float,
    previous_odometer: int | None,
) -> int:
    """Calculate km driven per liter from the previous fill-up."""
    if (
        previous_odometer is not None
        and odometer > previous_odometer
        and liters > 0
    ):
        km_driven = odometer - previous_odometer
        return round(km_driven / liters)
    return 0


def sync_vehicle_odometer(vehicle: Vehicle, odometer: int) -> None:
    """Keep vehicle odometer in sync with the latest fuel log reading."""
    if odometer > vehicle.current_odometer:
        vehicle.current_odometer = odometer


@router.post("/", response_model=FuelLogResponse, status_code=status.HTTP_201_CREATED)
async def create_fuel_log(
    fuel_log: FuelLogCreate,
    vehicle_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FuelLogResponse:
    """Create a new fuel log"""
    db_vehicle = await verify_vehicle_ownership(vehicle_id, current_user, db)
    liters = fuel_log.total_cost / fuel_log.price_per_liter

    previous_fuel_log = await get_previous_fuel_log(
        db,
        vehicle_id,
        fuel_log.date,
        fuel_log.odometer,
    )
    previous_odometer = resolve_previous_odometer(
        fuel_log.odometer,
        previous_fuel_log,
        db_vehicle,
    )
    mileage = calculate_mileage(fuel_log.odometer, liters, previous_odometer)

    db_fuel_log = FuelLog(
        **fuel_log.model_dump(),
        vehicle_id=vehicle_id,
        liters=liters,
        mileage=mileage,
    )
    db.add(db_fuel_log)
    sync_vehicle_odometer(db_vehicle, fuel_log.odometer)
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
        .order_by(FuelLog.date.desc())
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

    mileage_fields = {"date", "odometer", "total_cost", "price_per_liter"}
    if mileage_fields & updates.keys():
        previous_fuel_log = await get_previous_fuel_log(
            db,
            vehicle_id,
            db_fuel_log.date,
            db_fuel_log.odometer,
            exclude_id=fuel_log_id,
        )
        previous_odometer = resolve_previous_odometer(
            db_fuel_log.odometer,
            previous_fuel_log,
            db_vehicle,
        )
        db_fuel_log.mileage = calculate_mileage(
            db_fuel_log.odometer,
            db_fuel_log.liters,
            previous_odometer,
        )

    if "odometer" in updates:
        sync_vehicle_odometer(db_vehicle, db_fuel_log.odometer)

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
    db_fuel_log = await get_owned_fuel_log(
        fuel_log_id,
        vehicle_id,
        current_user,
        db,
    )
    await db.delete(db_fuel_log)
    await db.commit()
    return None
