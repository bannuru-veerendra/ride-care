"""Fuel mileage timeline validation and recalculation."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fuel_log import FuelLog
from app.models.vehicle import Vehicle


async def recalculate_vehicle_fuel_mileage(
    db: AsyncSession,
    vehicle_id: uuid.UUID,
    vehicle: Vehicle,
) -> None:
    """Validate timeline and recalculate mileage for all fill-ups."""
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
            (fuel_log.odometer - previous_odometer) / fuel_log.liters,
            1,
        )
        previous_odometer = fuel_log.odometer
        previous_label = f"the previous fill-up ({fuel_log.odometer})"
