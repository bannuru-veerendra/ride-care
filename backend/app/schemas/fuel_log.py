import uuid
from datetime import date as dt_date

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.utils.dates import app_today
from app.utils.numbers import round_2


def _normalize_2dp(value: object) -> object:
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, (int, float, str)):
        return round_2(float(value))
    return value


class FuelLogCreate(BaseModel):
    """Request body for POST /fuel_logs"""
    date: dt_date
    odometer: float
    total_cost: float
    price_per_liter: float
    notes: str | None = None

    @field_validator("odometer", "total_cost", "price_per_liter", mode="before")
    @classmethod
    def normalize_decimals(cls, value: object) -> object:
        return _normalize_2dp(value)

    @model_validator(mode="after")
    def validate_values(self):
        if self.date > app_today():
            raise ValueError("Fuel log date cannot be in the future")
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
    odometer: float | None = None
    total_cost: float | None = None
    price_per_liter: float | None = None
    notes: str | None = None

    @field_validator("odometer", "total_cost", "price_per_liter", mode="before")
    @classmethod
    def normalize_decimals(cls, value: object) -> object:
        return _normalize_2dp(value)

    @model_validator(mode="after")
    def validate_values(self):
        if self.date is not None and self.date > app_today():
            raise ValueError("Fuel log date cannot be in the future")
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
    odometer: float
    total_cost: float
    price_per_liter: float
    liters: float
    mileage: float | None = None
    notes: str | None = None

    @field_validator(
        "odometer",
        "total_cost",
        "price_per_liter",
        "liters",
        "mileage",
        mode="before",
    )
    @classmethod
    def normalize_decimals(cls, value: object) -> object:
        return _normalize_2dp(value)

    model_config = ConfigDict(from_attributes=True)
