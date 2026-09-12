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


class ServiceLogCreate(BaseModel):
    """Request body for POST /service_logs"""
    date: dt_date
    odometer: float
    service_center: str | None = None
    total_cost: float
    services_done: list[str]
    next_service_date: dt_date | None = None
    next_service_odometer: float | None = None
    notes: str | None = None

    @field_validator("odometer", "total_cost", "next_service_odometer", mode="before")
    @classmethod
    def normalize_decimals(cls, value: object) -> object:
        return _normalize_2dp(value)

    @model_validator(mode="after")
    def validate_values(self):
        if self.date > app_today():
            raise ValueError("Service log date cannot be in the future")
        if self.total_cost <= 0:
            raise ValueError("Total cost must be greater than 0")
        if self.odometer <= 0:
            raise ValueError("Odometer must be greater than 0")
        if not self.services_done:
            raise ValueError("At least one service must be done")
        if self.next_service_odometer is not None and self.next_service_odometer <= self.odometer:
            raise ValueError("Next service odometer must be greater than the current odometer")
        return self


class ServiceLogUpdate(BaseModel):
    """Request body for PATCH /service_logs/{service_log_id}"""
    date: dt_date | None = None
    odometer: float | None = None
    service_center: str | None = None
    total_cost: float | None = None
    services_done: list[str] | None = None
    next_service_date: dt_date | None = None
    next_service_odometer: float | None = None
    notes: str | None = None

    @field_validator("odometer", "total_cost", "next_service_odometer", mode="before")
    @classmethod
    def normalize_decimals(cls, value: object) -> object:
        return _normalize_2dp(value)

    @model_validator(mode="after")
    def validate_values(self):
        if self.date is not None and self.date > app_today():
            raise ValueError("Service log date cannot be in the future")
        if self.total_cost is not None and self.total_cost <= 0:
            raise ValueError("Total cost must be greater than 0")
        if self.odometer is not None and self.odometer <= 0:
            raise ValueError("Odometer must be greater than 0")
        if self.services_done is not None and not self.services_done:
            raise ValueError("At least one service must be done")
        if (
            self.next_service_odometer is not None
            and self.odometer is not None
            and self.next_service_odometer <= self.odometer
        ):
            raise ValueError("Next service odometer must be greater than the current odometer")
        return self


class ServiceLogResponse(BaseModel):
    """Response body for service log endpoints"""
    id: uuid.UUID
    vehicle_id: uuid.UUID
    date: dt_date
    odometer: float
    service_center: str | None = None
    total_cost: float
    services_done: list[str]
    next_service_date: dt_date | None = None
    next_service_odometer: float | None = None
    notes: str | None = None

    @field_validator("odometer", "total_cost", "next_service_odometer", mode="before")
    @classmethod
    def normalize_decimals(cls, value: object) -> object:
        return _normalize_2dp(value)

    model_config = ConfigDict(from_attributes=True)


class SuggestNextDueRequest(BaseModel):
    """Body for POST /service_logs/suggest-next-due"""
    date: dt_date
    odometer: float
    services_done: list[str]

    @field_validator("odometer", mode="before")
    @classmethod
    def normalize_decimals(cls, value: object) -> object:
        return _normalize_2dp(value)

    @model_validator(mode="after")
    def validate_values(self):
        if self.odometer <= 0:
            raise ValueError("Odometer must be greater than 0")
        if not self.services_done:
            raise ValueError("At least one service must be done")
        return self


class SuggestNextDueResponse(BaseModel):
    next_service_date: dt_date | None = None
    next_service_odometer: float | None = None
    matched_tasks: list[str] = []

    @field_validator("next_service_odometer", mode="before")
    @classmethod
    def normalize_decimals(cls, value: object) -> object:
        return _normalize_2dp(value)
