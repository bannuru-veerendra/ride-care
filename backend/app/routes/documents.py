import logging
import uuid
from datetime import date as dt_date

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.document import Document, DocumentType
from app.models.user import User
from app.schemas.document import DocumentResponse
from app.schemas.pagination import CursorPage
from app.utils.auth_dependency import get_current_user
from app.utils.cache import cache_delete, vehicle_health_key, vehicle_summary_key
from app.utils.document_records import (
    abort_pending_update,
    clean_optional_str,
    compensate_failed_create,
    get_owned_document,
    snapshot_document,
    to_document_response,
    validate_document_fields,
)
from app.utils.document_types import document_allows_expiry
from app.utils.pagination import paginate
from app.utils.redis_client import get_redis
from app.utils.storage import (
    cleanup_document,
    delete_document as delete_storage_document,
    relocate_document_type,
    upload_document,
)
from app.utils.vehicle_access import verify_vehicle_ownership

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    vehicle_id: uuid.UUID,
    document_type: DocumentType = Form(...),
    custom_label: str | None = Form(None),
    identifier: str | None = Form(None),
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
        custom_label, identifier, expiry_date = validate_document_fields(
            document_type=document_type,
            custom_label=custom_label,
            identifier=identifier,
            expiry_date=expiry_date,
        )
        notes = clean_optional_str(notes)

        await verify_vehicle_ownership(vehicle_id, current_user, db)
        storage_path = await upload_document(file, vehicle_id, document_type.value)

        db_document = Document(
            vehicle_id=vehicle_id,
            document_type=document_type,
            storage_path=storage_path,
            custom_label=custom_label,
            identifier=identifier,
            expiry_date=expiry_date,
            notes=notes,
        )
        db.add(db_document)
        await db.commit()
        committed = True
        await db.refresh(db_document)
        await cache_delete(
            redis,
            vehicle_summary_key(str(vehicle_id)),
            vehicle_health_key(str(vehicle_id)),
        )

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


@router.get("/", response_model=CursorPage[DocumentResponse])
async def get_documents(
    vehicle_id: uuid.UUID,
    cursor: str | None = Query(None),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CursorPage[DocumentResponse]:
    """Get paginated documents for a vehicle (newest first)."""
    await verify_vehicle_ownership(vehicle_id, current_user, db)

    try:
        page = await paginate(
            db,
            Document,
            filter_clause=Document.vehicle_id == vehicle_id,
            order_by_column=Document.created_at,
            cursor_column=Document.created_at,
            tiebreaker_column=Document.id,
            cursor=cursor,
            size=size,
            descending=True,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    items = [await to_document_response(db_document) for db_document in page.items]
    return CursorPage(
        items=items,
        next_cursor=page.next_cursor,
        has_more=page.has_more,
        total=page.total,
    )


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
    custom_label: str | None = Form(None),
    identifier: str | None = Form(None),
    expiry_date: dt_date | None = Form(None),
    notes: str | None = Form(None),
    clear_expiry_date: bool = Form(False),
    clear_notes: bool = Form(False),
    clear_identifier: bool = Form(False),
    clear_custom_label: bool = Form(False),
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
    has_identifier = identifier is not None or clear_identifier
    has_custom_label = custom_label is not None or clear_custom_label
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
    if clear_identifier and identifier is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide either identifier or clear_identifier, not both",
        )
    if clear_custom_label and custom_label is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide either custom_label or clear_custom_label, not both",
        )

    if (
        not has_file
        and not has_expiry
        and not has_notes
        and not has_type
        and not has_identifier
        and not has_custom_label
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide at least one field to update",
        )

    target_document_type = (
        document_type if document_type is not None else db_document.document_type
    )

    next_custom_label = db_document.custom_label
    if clear_custom_label:
        next_custom_label = None
    elif custom_label is not None:
        next_custom_label = custom_label

    next_identifier = db_document.identifier
    if clear_identifier:
        next_identifier = None
    elif identifier is not None:
        next_identifier = identifier

    next_expiry = db_document.expiry_date
    if clear_expiry_date:
        next_expiry = None
    elif expiry_date is not None:
        next_expiry = expiry_date

    # Switching to RC always drops expiry even if the client forgot to clear it.
    if not document_allows_expiry(target_document_type):
        next_expiry = None

    next_custom_label, next_identifier, next_expiry = validate_document_fields(
        document_type=target_document_type,
        custom_label=next_custom_label,
        identifier=next_identifier,
        expiry_date=next_expiry,
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

        db_document.custom_label = next_custom_label
        db_document.identifier = next_identifier
        db_document.expiry_date = next_expiry

        if clear_notes:
            db_document.notes = None
        elif notes is not None:
            db_document.notes = clean_optional_str(notes)

        await db.commit()
        await db.refresh(db_document)
        await cache_delete(
            redis,
            vehicle_summary_key(str(vehicle_id)),
            vehicle_health_key(str(vehicle_id)),
        )

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
        await cache_delete(
            redis,
            vehicle_summary_key(str(vehicle_id)),
            vehicle_health_key(str(vehicle_id)),
        )
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
