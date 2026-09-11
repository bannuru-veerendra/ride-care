import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.fuel_log import FuelLog
from app.models.user import User
from app.models.vehicle import Vehicle
from app.schemas.csv_import import CsvImportResponse
from app.schemas.fuel_log import (
    FuelLogCreate,
    FuelLogResponse,
    FuelLogUpdate,
)
from app.schemas.pagination import CursorPage
from app.utils.auth_dependency import get_current_user
from app.utils.vehicle_access import verify_vehicle_ownership
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
    fuel_log_csv_rows,
)
from app.utils.fuel_mileage import recalculate_vehicle_fuel_mileage
from app.utils.import_csv import (
    mileage_failure_detail,
    parse_fuel_csv,
    raise_csv_import_errors,
    require_csv_text,
)
from app.utils.pagination import paginate
from app.utils.redis_client import get_redis


router = APIRouter(prefix="/fuel_logs", tags=["fuel_logs"])


async def _invalidate_fuel_derived_caches(
    redis: Redis,
    vehicle_id: uuid.UUID,
    owner_id: uuid.UUID,
) -> None:
    """Drop caches that depend on fuel log aggregates / live odometer."""
    await cache_delete(
        redis,
        vehicle_detail_key(str(vehicle_id)),
        vehicle_summary_key(str(vehicle_id)),
        vehicle_analytics_key(str(vehicle_id)),
    )
    await cache_delete_pattern(redis, f"cache:vehicles:user:{owner_id}*")


async def get_owned_fuel_log(
    fuel_log_id: uuid.UUID,
    vehicle_id: uuid.UUID,
    current_user: User,
    db: AsyncSession,
) -> FuelLog:
    """Fetch a fuel log owned by the current user via vehicle ownership"""
    result = await db.execute(
        select(FuelLog)
        .join(Vehicle)
        .where(
            FuelLog.id == fuel_log_id,
            FuelLog.vehicle_id == vehicle_id,
            Vehicle.owner_id == current_user.id,
        )
    )
    db_fuel_log = result.scalar_one_or_none()
    if not db_fuel_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fuel log not found",
        )
    return db_fuel_log


@router.post("/", response_model=FuelLogResponse, status_code=status.HTTP_201_CREATED)
async def create_fuel_log(
    fuel_log: FuelLogCreate,
    vehicle_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> FuelLogResponse:
    """Create a new fuel log"""
    db_vehicle = await verify_vehicle_ownership(vehicle_id, current_user, db)
    db_fuel_log = FuelLog(
        **fuel_log.model_dump(),
        vehicle_id=vehicle_id,
        liters=round(fuel_log.total_cost / fuel_log.price_per_liter, 2),
    )
    db.add(db_fuel_log)
    await db.flush()
    await recalculate_vehicle_fuel_mileage(db, vehicle_id, db_vehicle)
    await db.commit()
    await db.refresh(db_fuel_log)
    await _invalidate_fuel_derived_caches(redis, vehicle_id, db_vehicle.owner_id)
    return db_fuel_log


@router.get("/", response_model=CursorPage[FuelLogResponse])
async def get_fuel_logs(
    vehicle_id: uuid.UUID,
    cursor: str | None = Query(None),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CursorPage[FuelLogResponse]:
    """Get paginated fuel logs for a vehicle"""
    await verify_vehicle_ownership(vehicle_id, current_user, db)

    try:
        return await paginate(
            db,
            FuelLog,
            filter_clause=FuelLog.vehicle_id == vehicle_id,
            order_by_column=FuelLog.date,
            cursor_column=FuelLog.date,
            tiebreaker_column=FuelLog.id,
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
async def export_fuel_logs_csv(
    vehicle_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Download all fuel logs for a vehicle as CSV (newest first)."""
    vehicle = await verify_vehicle_ownership(vehicle_id, current_user, db)
    result = await db.execute(
        select(FuelLog)
        .where(FuelLog.vehicle_id == vehicle_id)
        .order_by(FuelLog.date.desc(), FuelLog.id.desc())
    )
    logs = list(result.scalars().all())
    csv_body = fuel_log_csv_rows(logs)
    filename = csv_download_filename(
        "fuel", vehicle.vehicle_name, str(vehicle_id)
    )
    return Response(
        content=csv_body,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": content_disposition_attachment(filename),
        },
    )


@router.post("/import", response_model=CsvImportResponse)
async def import_fuel_logs_csv(
    vehicle_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> CsvImportResponse:
    """
    Bulk-import fuel fill-ups from an export-compatible CSV.
    All-or-nothing: validation or mileage failures import nothing.
    liters / mileage columns are ignored and recalculated server-side.
    Does not dedupe against existing logs — conflicting odometers fail the import.
    """
    db_vehicle = await verify_vehicle_ownership(vehicle_id, current_user, db)
    text = await require_csv_text(file)

    parsed = parse_fuel_csv(text)
    raise_csv_import_errors(parsed.errors)

    # Oldest first so timeline validation matches mileage order
    ordered = sorted(
        parsed.rows,
        key=lambda parsed_row: (
            parsed_row.payload.date,
            parsed_row.payload.odometer,
        ),
    )
    for parsed_row in ordered:
        fuel_log = parsed_row.payload
        db.add(
            FuelLog(
                **fuel_log.model_dump(),
                vehicle_id=vehicle_id,
                liters=round(fuel_log.total_cost / fuel_log.price_per_liter, 2),
            )
        )

    try:
        await db.flush()
        await recalculate_vehicle_fuel_mileage(db, vehicle_id, db_vehicle)
        await db.commit()
    except HTTPException as exc:
        await db.rollback()
        if isinstance(exc.detail, str):
            raise HTTPException(
                status_code=exc.status_code,
                detail=mileage_failure_detail(exc.detail, ordered),
            ) from exc
        raise
    except Exception:
        await db.rollback()
        raise

    await _invalidate_fuel_derived_caches(redis, vehicle_id, db_vehicle.owner_id)
    return CsvImportResponse(imported=len(ordered), errors=[])


@router.get("/{fuel_log_id}", response_model=FuelLogResponse)
async def get_fuel_log(
    fuel_log_id: uuid.UUID,
    vehicle_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FuelLogResponse:
    """Get a fuel log by ID"""
    return await get_owned_fuel_log(
        fuel_log_id,
        vehicle_id,
        current_user,
        db,
    )


@router.patch("/{fuel_log_id}", response_model=FuelLogResponse)
async def update_fuel_log(
    fuel_log_id: uuid.UUID,
    fuel_log: FuelLogUpdate,
    vehicle_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> FuelLogResponse:
    """Update a fuel log by ID"""
    db_vehicle = await verify_vehicle_ownership(vehicle_id, current_user, db)
    db_fuel_log = await get_owned_fuel_log(
        fuel_log_id,
        vehicle_id,
        current_user,
        db,
    )

    updates = fuel_log.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(db_fuel_log, key, value)

    if "total_cost" in updates or "price_per_liter" in updates:
        db_fuel_log.liters = round(
            db_fuel_log.total_cost / db_fuel_log.price_per_liter,
            2,
        )

    if {"date", "odometer", "total_cost", "price_per_liter"} & updates.keys():
        await db.flush()
        await recalculate_vehicle_fuel_mileage(db, vehicle_id, db_vehicle)

    await db.commit()
    await db.refresh(db_fuel_log)
    await _invalidate_fuel_derived_caches(redis, vehicle_id, db_vehicle.owner_id)
    return db_fuel_log


@router.delete("/{fuel_log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_fuel_log(
    fuel_log_id: uuid.UUID,
    vehicle_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> None:
    """Delete a fuel log by ID"""
    db_vehicle = await verify_vehicle_ownership(vehicle_id, current_user, db)
    db_fuel_log = await get_owned_fuel_log(
        fuel_log_id,
        vehicle_id,
        current_user,
        db,
    )
    await db.delete(db_fuel_log)
    await db.flush()
    await recalculate_vehicle_fuel_mileage(db, vehicle_id, db_vehicle)
    await db.commit()
    await _invalidate_fuel_derived_caches(redis, vehicle_id, db_vehicle.owner_id)
    return None
