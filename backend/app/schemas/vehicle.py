import uuid
from datetime import date, datetime

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator

from app.schemas.fuel_log import FuelLogResponse
from app.schemas.service_log import ServiceLogResponse


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


class VehicleSummaryResponse(BaseModel):
    """Aggregated dashboard stats for a single vehicle"""
    vehicle_id: uuid.UUID
    fuel_log_count: int
    average_mileage: float | None
    this_month_spend: float
    last_month_spend: float
    this_month_mileage: float | None
    last_month_mileage: float | None
    # Last two calendar months that have fill-ups with mileage (may skip empty months)
    recent_filled_month_mileage: float | None = None
    prior_filled_month_mileage: float | None = None
    recent_filled_month_label: str | None = None
    prior_filled_month_label: str | None = None
    recent_fuel_logs: list[FuelLogResponse]
    next_service: ServiceLogResponse | None = None


class MileageTrendPoint(BaseModel):
    """Single point on the mileage trend chart."""
    date: date
    date_label: str
    mileage: float
    odometer: int


class MonthlySpendPoint(BaseModel):
    """Monthly fuel spend bucket for the bar chart."""
    month: str
    year_month: str
    spend: float
    liters: float


class VehicleAnalyticsResponse(BaseModel):
    """Full analytics payload for the vehicle Analytics tab."""
    vehicle_id: uuid.UUID
    total_spend: float
    total_liters: float
    avg_mileage: float | None
    best_mileage: float | None
    worst_mileage: float | None
    total_fill_ups: int
    mileage_trend: list[MileageTrendPoint]
    monthly_spend: list[MonthlySpendPoint]
