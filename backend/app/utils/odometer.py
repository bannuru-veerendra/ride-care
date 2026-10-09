"""Live and earliest odometer reads shared by garage routes."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fuel_log import FuelLog
from app.models.service_log import ServiceLog
from app.models.vehicle import Vehicle
from app.utils.numbers import round_2


async def get_live_odometers_map(
    db: AsyncSession,
    vehicles: list[Vehicle],
) -> dict[uuid.UUID, float]:
    """Return live odometer for each vehicle in one round-trip."""
    if not vehicles:
        return {}

    vehicle_ids = [vehicle.id for vehicle in vehicles]
    baselines = {
        vehicle.id: round_2(float(vehicle.current_odometer or 0))
        for vehicle in vehicles
    }
    log_max_by_vehicle: dict[uuid.UUID, float] = {}

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
        log_max_by_vehicle[vehicle_id] = round_2(float(odometer or 0))

    return {
        vehicle_id: round_2(
            max(
                baselines[vehicle_id],
                log_max_by_vehicle.get(vehicle_id) or 0.0,
            )
        )
        for vehicle_id in vehicle_ids
    }


async def get_live_odometer(
    db: AsyncSession,
    vehicle: Vehicle,
) -> float:
    """Return the highest known odometer for a vehicle."""
    live_odometers = await get_live_odometers_map(db, [vehicle])
    return live_odometers[vehicle.id]


async def get_min_log_odometer(
    db: AsyncSession,
    vehicle_id: uuid.UUID,
) -> float | None:
    """Return the lowest fuel/service odometer for a vehicle, if any."""
    fuel_result = await db.execute(
        select(func.min(FuelLog.odometer)).where(FuelLog.vehicle_id == vehicle_id)
    )
    service_result = await db.execute(
        select(func.min(ServiceLog.odometer)).where(
            ServiceLog.vehicle_id == vehicle_id
        )
    )
    fuel_min = fuel_result.scalar_one_or_none()
    service_min = service_result.scalar_one_or_none()
    candidates = [
        round_2(float(value))
        for value in (fuel_min, service_min)
        if value is not None
    ]
    if not candidates:
        return None
    return min(candidates)
