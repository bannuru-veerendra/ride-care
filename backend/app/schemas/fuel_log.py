import uuid
from datetime import date as dt_date

from pydantic import BaseModel, model_validator


class FuelLogCreate(BaseModel):
    """Request body for POST /fuel_logs"""
    date: dt_date
    odometer: int
    total_cost: float
    price_per_liter: float
    notes: str | None = None

    @model_validator(mode="after")
    def validate_values(self):
        if self.total_cost <= 0:
            raise ValueError("Total cost must be greater than 0")
        if self.price_per_liter <= 0:
            raise ValueError("Price per liter must be greater than 0")
        if self.odometer <= 0:
            raise ValueError("Odometer must be greater than 0")
        return self


class FuelLogUpdate(BaseModel):
    """Request body for PATCH /fuel_logs/{fuel_log_id}"""
    date: dt_date | None = None
    odometer: int | None = None
    total_cost: float | None = None
    price_per_liter: float | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def validate_values(self):
        if self.total_cost is not None and self.total_cost <= 0:
            raise ValueError("Total cost must be greater than 0")
        if self.price_per_liter is not None and self.price_per_liter <= 0:
            raise ValueError("Price per liter must be greater than 0")
        if self.odometer is not None and self.odometer <= 0:
            raise ValueError("Odometer must be greater than 0")
        return self


class FuelLogResponse(BaseModel):
    """Response body for fuel log endpoints"""
    id: uuid.UUID
    vehicle_id: uuid.UUID
    date: dt_date
    odometer: int
    total_cost: float
    price_per_liter: float
    liters: float
    mileage: int
    notes: str | None = None

    class Config:
        from_attributes = True
