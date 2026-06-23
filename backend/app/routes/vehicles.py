from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.extensions import get_db
from app.models.vehicle import Vehicle
from app.models.user import User
from app.schemas.vehicle import VehicleCreate, VehicleUpdate, VehicleResponse
from app.utils.auth_dependency import get_current_user

router = APIRouter(prefix="/vehicles", tags=["vehicles"])

@router.post("/", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
async def create_vehicle(vehicle: VehicleCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> VehicleResponse:
    """Create a new vehicle"""
    result = await db.execute(select(Vehicle).where(Vehicle.registration_number == vehicle.registration_number))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vehicle with this registration number already exists")

    vehicle = Vehicle(**vehicle.model_dump(), owner_id=current_user.id)
    db.add(vehicle)
    await db.commit()
    await db.refresh(vehicle)
    return vehicle


@router.get("/", response_model=list[VehicleResponse])
async def get_vehicle(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> list[VehicleResponse]:
    """Get all vehicles for the current user"""
    result = await db.execute(select(Vehicle).where(Vehicle.owner_id == current_user.id))
    db_vehicles = result.scalars().all()
    if not db_vehicles:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No vehicles found")
    return db_vehicles


@router.get("/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(vehicle_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> VehicleResponse:
    """Get a vehicle by ID"""
    result = await db.execute(select(Vehicle).where(Vehicle.id == vehicle_id, Vehicle.owner_id == current_user.id))
    db_vehicle = result.scalar_one_or_none()
    if not db_vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
    return db_vehicle


@router.patch("/{vehicle_id}", response_model=VehicleResponse)
async def update_vehicle(vehicle_id: uuid.UUID, vehicle: VehicleUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> VehicleResponse:
    """Update a vehicle"""
    result = await db.execute(select(Vehicle).where(Vehicle.id == vehicle_id, Vehicle.owner_id == current_user.id))
    
    db_vehicle = result.scalar_one_or_none()
    if not db_vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
    
    for key, value in vehicle.model_dump(exclude_unset=True).items():
        setattr(db_vehicle, key, value)

    await db.commit()
    await db.refresh(db_vehicle)
    return db_vehicle


@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vehicle(vehicle_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> None:
    """Delete a vehicle"""
    result = await db.execute(select(Vehicle).where(Vehicle.id == vehicle_id, Vehicle.owner_id == current_user.id))
    db_vehicle = result.scalar_one_or_none()
    if not db_vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
    await db.delete(db_vehicle)
    await db.commit()
    return None