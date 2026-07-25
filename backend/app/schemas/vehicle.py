import uuid
from datetime import datetime

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator


class VehicleCreate(BaseModel):
    """Request body for POST /vehicles"""
    brand: str
    vehicle_name: str
    year: int
    registration_number: str
    baseline_odometer: int = Field(
        default=0,
        validation_alias=AliasChoices("baseline_odometer", "current_odometer"),
    )

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode="after")
    def validate_values(self):
        current_year = datetime.now().year
        if self.year < 1886 or self.year > current_year:
            raise ValueError(f"Year must be between 1886 and {current_year}")
        if self.baseline_odometer < 0:
            raise ValueError("Odometer cannot be negative")
        return self


class VehicleUpdate(BaseModel):
    """Request body for PATCH /vehicles/{vehicle_id}"""
    brand: str | None = None
    vehicle_name: str | None = None
    year: int | None = None
    registration_number: str | None = None
    baseline_odometer: int | None = Field(
        default=None,
        validation_alias=AliasChoices("baseline_odometer", "current_odometer"),
    )

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode="after")
    def validate_values(self):
        current_year = datetime.now().year
        if self.year is not None and (self.year < 1886 or self.year > current_year):
            raise ValueError(f"Year must be between 1886 and {current_year}")
        if self.baseline_odometer is not None and self.baseline_odometer < 0:
            raise ValueError("Odometer cannot be negative")
        return self


class VehicleResponse(BaseModel):
    """Response body for vehicle endpoints"""
    id: uuid.UUID
    owner_id: uuid.UUID
    brand: str
    vehicle_name: str
    year: int
    registration_number: str
    baseline_odometer: int
    current_odometer: int

    model_config = ConfigDict(from_attributes=True)
