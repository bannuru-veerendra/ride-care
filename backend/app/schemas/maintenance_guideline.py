from pydantic import BaseModel


class MaintenanceGuidelineResponse(BaseModel):
    """Public response for a maintenance guideline."""

    id: str
    component: str
    task: str
    interval_km: int | None
    interval_months: int | None
    description: str
    severity: str
    sort_order: int
