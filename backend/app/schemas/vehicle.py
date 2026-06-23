from pydantic import BaseModel
import uuid

class VehicleCreate(BaseModel):
    """Request body for POST /vehicles"""
    brand: str
    vehicle_name: str
    year: int
    registration_number: str
    current_odometer: int = 0

class VehicleUpdate(BaseModel):
    """Request body for PUT /vehicles/{vehicle_id}"""
    brand: str | None = None
    vehicle_name: str | None = None
    year: int | None = None
    registration_number: str | None = None
    current_odometer: int | None = None

class VehicleResponse(BaseModel):
    """Response body for GET /vehicles/{vehicle_id}"""
    id: uuid.UUID
    brand: str
    vehicle_name: str
    year: int
    registration_number: str
    current_odometer: int
    
    class Config:
        from_attributes = True