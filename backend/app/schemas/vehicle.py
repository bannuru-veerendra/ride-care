import uuid

from pydantic import BaseModel, model_validator


class VehicleCreate(BaseModel):
    """Request body for POST /vehicles"""
    brand: str
    vehicle_name: str
    year: int
    registration_number: str
    current_odometer: int = 0

    @model_validator(mode="after")
    def validate_values(self):
        if self.year < 1886 or self.year > 2100:
            raise ValueError("Year must be between 1886 and 2100")
        if self.current_odometer < 0:
            raise ValueError("Odometer cannot be negative")
        return self


class VehicleUpdate(BaseModel):
    """Request body for PATCH /vehicles/{vehicle_id}"""
    brand: str | None = None
    vehicle_name: str | None = None
    year: int | None = None
    registration_number: str | None = None
    current_odometer: int | None = None

    @model_validator(mode="after")
    def validate_values(self):
        if self.year is not None and (self.year < 1886 or self.year > 2100):
            raise ValueError("Year must be between 1886 and 2100")
        if self.current_odometer is not None and self.current_odometer < 0:
            raise ValueError("Odometer cannot be negative")
        return self


class VehicleResponse(BaseModel):
    """Response body for GET /vehicles/{vehicle_id}"""
    id: uuid.UUID
    owner_id: uuid.UUID
    brand: str
    vehicle_name: str
    year: int
    registration_number: str
    current_odometer: int

    class Config:
        from_attributes = True
