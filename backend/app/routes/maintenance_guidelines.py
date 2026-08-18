from fastapi import APIRouter, Depends, Query

from app.data.guidelines import load_guidelines
from app.models.user import User
from app.schemas.maintenance_guideline import MaintenanceGuidelineResponse
from app.utils.auth_dependency import get_current_user

router = APIRouter(
    prefix="/maintenance-guidelines",
    tags=["maintenance guidelines"],
)


@router.get("/", response_model=list[MaintenanceGuidelineResponse])
async def get_guidelines(
    severity: str | None = Query(
        None,
        description="Filter by severity: critical, high, medium, low",
    ),
    component: str | None = Query(
        None,
        description="Filter by component e.g. Engine, Brakes, Tyres",
    ),
    current_user: User = Depends(get_current_user),
) -> list[MaintenanceGuidelineResponse]:
    """
    Get all maintenance guidelines sorted by sort_order.
    Data loaded from JSON file — no DB query, no Redis needed.
    Supports optional filtering by severity and component.
    """
    guidelines = load_guidelines()

    if severity:
        guidelines = [g for g in guidelines if g["severity"] == severity]
    if component:
        guidelines = [
            g for g in guidelines if g["component"].lower() == component.lower()
        ]

    return guidelines


@router.get("/components", response_model=list[str])
async def get_components(
    current_user: User = Depends(get_current_user),
) -> list[str]:
    """
    Get unique component names for filter dropdowns.
    Order preserved — matches sort_order of guidelines.
    """
    guidelines = load_guidelines()
    # dict.fromkeys preserves insertion order and deduplicates
    return list(dict.fromkeys(g["component"] for g in guidelines))


@router.get("/severity-levels", response_model=list[str])
async def get_severity_levels(
    current_user: User = Depends(get_current_user),
) -> list[str]:
    """
    Get available severity levels in priority order.
    Used to populate filter dropdowns on the frontend.
    """
    return ["critical", "high", "medium", "low"]
