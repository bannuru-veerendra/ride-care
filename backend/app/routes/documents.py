import logging
import uuid
from datetime import date as dt_date

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.document import Document, DocumentType
from app.models.user import User
from app.models.vehicle import Vehicle
from app.schemas.document import DocumentResponse, _DocumentDbFields
from app.utils.auth_dependency import get_current_user
from app.utils.cache import cache_delete, vehicle_summary_key
from app.utils.dates import app_today
from app.utils.redis_client import get_redis
from app.utils.reminders import document_expiry_fields
from app.utils.storage import (
    cleanup_document,
    delete_document as delete_storage_document,
    get_signed_url,
    move_document,
    relocate_document_type,
    upload_document,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])


async def verify_vehicle_ownership(
    vehicle_id: uuid.UUID,
    current_user: User,
    db: AsyncSession,
) -> Vehicle:
    """Verify that the current user owns the vehicle."""
    result = await db.execute(
        select(Vehicle).where(
            Vehicle.id == vehicle_id,
            Vehicle.owner_id == current_user.id,
        )
    )
    db_vehicle = result.scalar_one_or_none()
    if not db_vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found",
        )
    return db_vehicle


async def get_owned_document(
    document_id: uuid.UUID,
    vehicle_id: uuid.UUID,
    current_user: User,
    db: AsyncSession,
) -> Document:
    """Fetch a document owned by the current user via vehicle ownership."""
    result = await db.execute(
        select(Document)
        .join(Vehicle)
        .where(
            Document.id == document_id,
            Document.vehicle_id == vehicle_id,
            Vehicle.owner_id == current_user.id,
        )
    )
    db_document = result.scalar_one_or_none()
    if not db_document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    return db_document


def snapshot_document(db_document: Document) -> dict:
    """Copy document fields so a failed delete can be rolled back in the DB."""
    return {
        "id": db_document.id,
        "vehicle_id": db_document.vehicle_id,
        "document_type": db_document.document_type,
        "storage_path": db_document.storage_path,
        "original_filename": db_document.original_filename,
        "expiry_date": db_document.expiry_date,
        "notes": db_document.notes,
    }


async def compensate_failed_create(
    db: AsyncSession,
    *,
    storage_path: str | None,
    db_document: Document | None,
    committed: bool,
) -> None:
    """Undo a partially completed create so DB and storage stay aligned."""
    if committed and db_document is not None:
        await db.delete(db_document)
        await db.commit()
    else:
        await db.rollback()

    if storage_path:
        await cleanup_document(storage_path)


async def abort_pending_update(
    db: AsyncSession,
    *,
    uploaded_path: str | None = None,
    old_storage_path: str | None = None,
    new_storage_path: str | None = None,
) -> None:
    """Undo storage side-effects from a failed document update."""
    await db.rollback()

    if uploaded_path:
        await cleanup_document(uploaded_path)
        return

    if old_storage_path and new_storage_path:
        try:
            await move_document(new_storage_path, old_storage_path)
        except Exception:
            logger.exception(
                "Failed to restore storage object from %s to %s",
                new_storage_path,
                old_storage_path,
            )


async def to_document_response(db_document: Document) -> DocumentResponse:
    """Build API response with a fresh signed URL and expiry urgency fields."""
    days_until, expiry_status = document_expiry_fields(
        db_document.expiry_date,
        today=app_today(),
    )
    return DocumentResponse(
        **_DocumentDbFields.model_validate(db_document).model_dump(),
        signed_url=await get_signed_url(db_document.storage_path),
        days_until=days_until,
        expiry_status=expiry_status,
    )


@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    vehicle_id: uuid.UUID,
    document_type: DocumentType = Form(...),
    expiry_date: dt_date | None = Form(None),
    notes: str | None = Form(None),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> DocumentResponse:
    """Upload a new document."""
    storage_path: str | None = None
    db_document: Document | None = None
    committed = False

    try:
        await verify_vehicle_ownership(vehicle_id, current_user, db)
        storage_path = await upload_document(file, vehicle_id, document_type.value)

        db_document = Document(
            vehicle_id=vehicle_id,
            document_type=document_type,
            storage_path=storage_path,
            original_filename=file.filename or "unknown",
            expiry_date=expiry_date,
            notes=notes,
        )
        db.add(db_document)
        await db.commit()
        committed = True
        await db.refresh(db_document)
        await cache_delete(redis, vehicle_summary_key(str(vehicle_id)))

        return await to_document_response(db_document)
    except Exception as exc:
        if storage_path is not None or committed:
            await compensate_failed_create(
                db,
                storage_path=storage_path,
                db_document=db_document,
                committed=committed,
            )
        if isinstance(exc, HTTPException):
            raise
        logger.exception("Failed to create document for vehicle %s", vehicle_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save document",
        ) from exc


@router.get("/", response_model=list[DocumentResponse])
async def get_documents(
    vehicle_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[DocumentResponse]:
    """Get all documents for a vehicle."""
    await verify_vehicle_ownership(vehicle_id, current_user, db)
    result = await db.execute(
        select(Document)
        .where(Document.vehicle_id == vehicle_id)
        .order_by(Document.created_at.desc())
    )
    db_documents = result.scalars().all()

    return [await to_document_response(db_document) for db_document in db_documents]


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: uuid.UUID,
    vehicle_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    """Get a document by ID."""
    db_document = await get_owned_document(document_id, vehicle_id, current_user, db)
    return await to_document_response(db_document)


@router.patch("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: uuid.UUID,
    vehicle_id: uuid.UUID,
    document_type: DocumentType | None = Form(None),
    expiry_date: dt_date | None = Form(None),
    notes: str | None = Form(None),
    clear_expiry_date: bool = Form(False),
    clear_notes: bool = Form(False),
    file: UploadFile | None = File(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> DocumentResponse:
    """Update document metadata, type, and/or replace the stored file."""
    db_document = await get_owned_document(document_id, vehicle_id, current_user, db)

    has_file = file is not None and bool(file.filename)
    has_expiry = expiry_date is not None or clear_expiry_date
    has_notes = notes is not None or clear_notes
    has_type = document_type is not None and document_type != db_document.document_type

    if clear_expiry_date and expiry_date is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide either expiry_date or clear_expiry_date, not both",
        )
    if clear_notes and notes is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide either notes or clear_notes, not both",
        )

    if not has_file and not has_expiry and not has_notes and not has_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide at least one field to update",
        )

    target_document_type = (
        document_type if document_type is not None else db_document.document_type
    )

    uploaded_path: str | None = None
    replaced_storage_path: str | None = None
    type_change_from: str | None = None
    type_change_to: str | None = None

    try:
        if has_file:
            replaced_storage_path = db_document.storage_path
            uploaded_path = await upload_document(
                file,
                vehicle_id,
                target_document_type.value,
            )
            db_document.storage_path = uploaded_path
            db_document.original_filename = file.filename or "unknown"

        elif has_type:
            type_change_from = db_document.storage_path
            type_change_to = await relocate_document_type(
                db_document.storage_path,
                vehicle_id,
                target_document_type.value,
            )
            db_document.storage_path = type_change_to

        if has_type:
            db_document.document_type = target_document_type

        if clear_expiry_date:
            db_document.expiry_date = None
        elif expiry_date is not None:
            db_document.expiry_date = expiry_date

        if clear_notes:
            db_document.notes = None
        elif notes is not None:
            db_document.notes = notes

        await db.commit()
        await db.refresh(db_document)
        await cache_delete(redis, vehicle_summary_key(str(vehicle_id)))

        if replaced_storage_path:
            await cleanup_document(replaced_storage_path)

        return await to_document_response(db_document)
    except Exception as exc:
        await abort_pending_update(
            db,
            uploaded_path=uploaded_path,
            old_storage_path=type_change_from,
            new_storage_path=type_change_to,
        )
        if isinstance(exc, HTTPException):
            raise
        logger.exception("Failed to update document %s", document_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update document",
        ) from exc


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID,
    vehicle_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> None:
    """Delete a document by ID."""
    db_document = await get_owned_document(document_id, vehicle_id, current_user, db)
    document_snapshot = snapshot_document(db_document)
    storage_path = db_document.storage_path

    try:
        await db.delete(db_document)
        await db.commit()
        await cache_delete(redis, vehicle_summary_key(str(vehicle_id)))
    except Exception as exc:
        await db.rollback()
        logger.exception("Failed to delete document record %s", document_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document",
        ) from exc

    try:
        await delete_storage_document(storage_path)
    except Exception as exc:
        logger.exception("Storage delete failed for %s", storage_path)
        try:
            db.add(Document(**document_snapshot))
            await db.commit()
        except Exception:
            await db.rollback()
            logger.exception(
                "Failed to restore document record %s after storage delete error",
                document_id,
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document",
        ) from exc

    return None
