import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.service_log import ServiceLog
from app.models.user import User
from app.models.vehicle import Vehicle
from app.schemas.csv_import import CsvImportResponse
from app.schemas.pagination import CursorPage
from app.schemas.service_log import (
    ServiceLogCreate,
    ServiceLogResponse,
    ServiceLogUpdate,
    SuggestNextDueRequest,
    SuggestNextDueResponse,
)
from app.utils.auth_dependency import get_current_user
from app.utils.auto_due import suggest_next_due
from app.utils.cache import (
    cache_delete,
    cache_delete_pattern,
    vehicle_analytics_key,
    vehicle_detail_key,
    vehicle_summary_key,
)
from app.utils.export_csv import (
    content_disposition_attachment,
    csv_download_filename,
    service_log_csv_rows,
)
from app.utils.import_csv import (
    CsvRowError,
    parse_service_csv,
    raise_csv_import_errors,
    require_csv_text,
)
from app.utils.pagination import paginate
from app.utils.redis_client import get_redis
from app.utils.reminders import find_active_next_service
from app.utils.vehicle_access import verify_vehicle_ownership


router = APIRouter(prefix="/service_logs", tags=["service_logs"])


@router.post("/suggest-next-due", response_model=SuggestNextDueResponse)
async def suggest_service_next_due(
    payload: SuggestNextDueRequest,
    current_user: User = Depends(get_current_user),
) -> SuggestNextDueResponse:
    """Suggest next-due date/km from maintenance catalog intervals for selected services."""
    _ = current_user
    suggestion = suggest_next_due(
        services_done=payload.services_done,
        visit_date=payload.date,
        visit_odometer=payload.odometer,
    )
    return SuggestNextDueResponse(
        next_service_date=suggestion.next_service_date,
        next_service_odometer=suggestion.next_service_odometer,
        matched_tasks=suggestion.matched_tasks,
    )


async def _invalidate_service_derived_caches(
    redis: Redis,
    vehicle_id: uuid.UUID,
    owner_id: uuid.UUID,
) -> None:
    """Drop caches that depend on service logs / live odometer."""
    await cache_delete(
        redis,
        vehicle_summary_key(str(vehicle_id)),
        vehicle_detail_key(str(vehicle_id)),
        vehicle_analytics_key(str(vehicle_id)),
    )
    await cache_delete_pattern(redis, f"cache:vehicles:user:{owner_id}*")


async def get_owned_service_log(
    service_log_id: uuid.UUID,
    vehicle_id: uuid.UUID,
    current_user: User,
    db: AsyncSession,
) -> ServiceLog:
    """Fetch a service log owned by the current user via vehicle ownership"""
    result = await db.execute(
        select(ServiceLog).join(Vehicle).where(
            ServiceLog.id == service_log_id,
            ServiceLog.vehicle_id == vehicle_id,
            Vehicle.owner_id == current_user.id,
        )
    )
    db_service_log = result.scalar_one_or_none()
    if not db_service_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service log not found",
        )
    return db_service_log


def _validate_next_service_odometer(
    odometer: float,
    next_service_odometer: float | None,
) -> None:
    if next_service_odometer is not None and next_service_odometer <= odometer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Next service odometer must be greater than the current odometer",
        )


def _service_odometer_below_baseline_message(
    odometer: float,
    baseline_odometer: float,
) -> str | None:
    """Return an error message when a service odometer is below vehicle baseline."""
    if odometer < baseline_odometer:
        return (
            f"Odometer reading ({odometer}) must be greater than or equal to "
            f"the vehicle's baseline odometer ({baseline_odometer})"
        )
    return None


def _validate_service_odometer_against_baseline(
    odometer: float,
    baseline_odometer: float,
) -> None:
    """Service readings feed live odometer — reject values below the vehicle baseline."""
    message = _service_odometer_below_baseline_message(odometer, baseline_odometer)
    if message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )


@router.post("/", response_model=ServiceLogResponse, status_code=status.HTTP_201_CREATED)
async def create_service_log(
    service_log: ServiceLogCreate,
    vehicle_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> ServiceLogResponse:
    """Create a new service log"""
    db_vehicle = await verify_vehicle_ownership(vehicle_id, current_user, db)
    _validate_service_odometer_against_baseline(
        service_log.odometer,
        db_vehicle.current_odometer,
    )
    db_service_log = ServiceLog(
        **service_log.model_dump(),
        vehicle_id=vehicle_id,
    )
    db.add(db_service_log)
    await db.commit()
    await db.refresh(db_service_log)
    await _invalidate_service_derived_caches(redis, vehicle_id, db_vehicle.owner_id)
    return db_service_log


@router.get("/", response_model=CursorPage[ServiceLogResponse])
async def get_service_logs(
    vehicle_id: uuid.UUID,
    cursor: str | None = Query(None),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CursorPage[ServiceLogResponse]:
    """Get paginated service logs for a vehicle"""
    await verify_vehicle_ownership(vehicle_id, current_user, db)

    try:
        return await paginate(
            db,
            ServiceLog,
            filter_clause=ServiceLog.vehicle_id == vehicle_id,
            order_by_column=ServiceLog.date,
            cursor_column=ServiceLog.date,
            tiebreaker_column=ServiceLog.id,
            cursor=cursor,
            size=size,
            descending=True,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get("/export")
async def export_service_logs_csv(
    vehicle_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Download all service logs for a vehicle as CSV (newest first)."""
    vehicle = await verify_vehicle_ownership(vehicle_id, current_user, db)
    result = await db.execute(
        select(ServiceLog)
        .where(ServiceLog.vehicle_id == vehicle_id)
        .order_by(ServiceLog.date.desc(), ServiceLog.id.desc())
    )
    logs = list(result.scalars().all())
    csv_body = service_log_csv_rows(logs)
    filename = csv_download_filename(
        "service", vehicle.vehicle_name, str(vehicle_id)
    )
    return Response(
        content=csv_body,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": content_disposition_attachment(filename),
        },
    )


@router.post("/import", response_model=CsvImportResponse)
async def import_service_logs_csv(
    vehicle_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> CsvImportResponse:
    """
    Bulk-import service visits from an export-compatible CSV.
    All-or-nothing: any row or baseline failure imports nothing.
    Does not dedupe against existing logs — conflicting rows fail the import.
    """
    db_vehicle = await verify_vehicle_ownership(vehicle_id, current_user, db)
    text = await require_csv_text(file)

    parsed = parse_service_csv(text)
    raise_csv_import_errors(parsed.errors)

    baseline_errors: list[CsvRowError] = []
    baseline = db_vehicle.current_odometer
    for parsed_row in parsed.rows:
        message = _service_odometer_below_baseline_message(
            parsed_row.payload.odometer,
            baseline,
        )
        if message:
            baseline_errors.append(
                CsvRowError(row=parsed_row.row, message=message)
            )
    raise_csv_import_errors(baseline_errors)

    for parsed_row in parsed.rows:
        db.add(
            ServiceLog(**parsed_row.payload.model_dump(), vehicle_id=vehicle_id)
        )

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    await _invalidate_service_derived_caches(redis, vehicle_id, db_vehicle.owner_id)
    return CsvImportResponse(imported=len(parsed.rows), errors=[])


@router.get("/next", response_model=ServiceLogResponse | None)
async def get_next_service_log(
    vehicle_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ServiceLogResponse | None:
    """Most recent service log with an active (unfulfilled) next due date or odometer."""
    await verify_vehicle_ownership(vehicle_id, current_user, db)

    result = await db.execute(
        select(ServiceLog)
        .where(ServiceLog.vehicle_id == vehicle_id)
        .order_by(ServiceLog.date.desc(), ServiceLog.odometer.desc())
    )
    return find_active_next_service(list(result.scalars().all()))


@router.get("/{service_log_id}", response_model=ServiceLogResponse)
async def get_service_log(
    service_log_id: uuid.UUID,
    vehicle_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ServiceLogResponse:
    """Get a service log by ID"""
    return await get_owned_service_log(
        service_log_id,
        vehicle_id,
        current_user,
        db,
    )


@router.patch("/{service_log_id}", response_model=ServiceLogResponse)
async def update_service_log(
    service_log_id: uuid.UUID,
    service_log: ServiceLogUpdate,
    vehicle_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> ServiceLogResponse:
    """Update a service log by ID"""
    db_vehicle = await verify_vehicle_ownership(vehicle_id, current_user, db)
    db_service_log = await get_owned_service_log(
        service_log_id,
        vehicle_id,
        current_user,
        db,
    )

    updates = service_log.model_dump(exclude_unset=True)
    merged_odometer = updates.get("odometer", db_service_log.odometer)
    merged_next = (
        updates["next_service_odometer"]
        if "next_service_odometer" in updates
        else db_service_log.next_service_odometer
    )
    _validate_service_odometer_against_baseline(
        merged_odometer,
        db_vehicle.current_odometer,
    )
    _validate_next_service_odometer(merged_odometer, merged_next)

    for key, value in updates.items():
        setattr(db_service_log, key, value)
    await db.commit()
    await db.refresh(db_service_log)
    await _invalidate_service_derived_caches(redis, vehicle_id, db_vehicle.owner_id)
    return db_service_log


@router.delete("/{service_log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service_log(
    service_log_id: uuid.UUID,
    vehicle_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> None:
    """Delete a service log by ID"""
    db_vehicle = await verify_vehicle_ownership(vehicle_id, current_user, db)
    db_service_log = await get_owned_service_log(
        service_log_id,
        vehicle_id,
        current_user,
        db,
    )
    await db.delete(db_service_log)
    await db.commit()
    await _invalidate_service_derived_caches(redis, vehicle_id, db_vehicle.owner_id)
    return None
