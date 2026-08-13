"""Shared vehicle ownership checks for vehicle-scoped routes."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.vehicle import Vehicle


async def verify_vehicle_ownership(
    vehicle_id: uuid.UUID,
    current_user: User,
    db: AsyncSession,
) -> Vehicle:
    """Return the vehicle if the current user owns it; otherwise 404."""
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
