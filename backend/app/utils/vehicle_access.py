"""Shared vehicle ownership checks for vehicle-scoped routes."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.vehicle import Vehicle


async def find_owned_vehicle(
    db: AsyncSession,
    vehicle_id: uuid.UUID,
    owner_id: uuid.UUID,
) -> Vehicle | None:
    """Return the vehicle when this user owns it."""
    result = await db.execute(
        select(Vehicle).where(
            Vehicle.id == vehicle_id,
            Vehicle.owner_id == owner_id,
        )
    )
    return result.scalar_one_or_none()


async def verify_vehicle_ownership(
    vehicle_id: uuid.UUID,
    current_user: User,
    db: AsyncSession,
) -> Vehicle:
    """Return the vehicle if the current user owns it; otherwise 404."""
    vehicle = await find_owned_vehicle(db, vehicle_id, current_user.id)
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found",
        )
    return vehicle
