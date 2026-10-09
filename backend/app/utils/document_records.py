"""Document field rules, ownership lookup, and storage rollback helpers."""

import logging
import uuid
from datetime import date as dt_date

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentType
from app.models.user import User
from app.models.vehicle import Vehicle
from app.schemas.document import DocumentResponse, _DocumentDbFields
from app.utils.dates import app_today
from app.utils.document_types import (
    MAX_DOCUMENT_TEXT_LENGTH,
    document_allows_expiry,
    document_display_label,
    document_requires_expiry,
)
from app.utils.reminders import document_expiry_fields
from app.utils import storage as storage_api

logger = logging.getLogger(__name__)


def clean_optional_str(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def validate_document_fields(
    *,
    document_type: DocumentType,
    custom_label: str | None,
    identifier: str | None,
    expiry_date: dt_date | None,
) -> tuple[str | None, str | None, dt_date | None]:
    """Normalize and validate type / label / identifier / expiry rules."""
    custom_label = clean_optional_str(custom_label)
    identifier = clean_optional_str(identifier)

    if custom_label and len(custom_label) > MAX_DOCUMENT_TEXT_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Custom document name must be at most {MAX_DOCUMENT_TEXT_LENGTH} characters",
        )
    if identifier and len(identifier) > MAX_DOCUMENT_TEXT_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Identifier must be at most {MAX_DOCUMENT_TEXT_LENGTH} characters",
        )

    if document_type == DocumentType.OTHER:
        if not custom_label:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Custom document name is required for Other",
            )
    else:
        custom_label = None

    if not document_allows_expiry(document_type):
        if expiry_date is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration Certificate does not have an expiry date",
            )
    elif document_requires_expiry(document_type):
        if expiry_date is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Expiry date is required for this document type",
            )

    return custom_label, identifier, expiry_date


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
        "custom_label": db_document.custom_label,
        "identifier": db_document.identifier,
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
        await storage_api.cleanup_document(storage_path)


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
        await storage_api.cleanup_document(uploaded_path)
        return

    if old_storage_path and new_storage_path:
        try:
            await storage_api.move_document(new_storage_path, old_storage_path)
        except Exception:
            logger.exception(
                "Failed to restore storage object from %s to %s",
                new_storage_path,
                old_storage_path,
            )


async def to_document_response(db_document: Document) -> DocumentResponse:
    """Build API response with a fresh signed URL and expiry urgency fields."""
    fields = _DocumentDbFields.model_validate(db_document).model_dump()
    if document_allows_expiry(db_document.document_type):
        days_until, expiry_status = document_expiry_fields(
            db_document.expiry_date,
            today=app_today(),
        )
    else:
        # RC (and any no-expiry type): never surface leftover DB expiry to clients.
        fields["expiry_date"] = None
        days_until, expiry_status = None, None

    return DocumentResponse(
        **fields,
        display_label=document_display_label(
            db_document.document_type,
            db_document.custom_label,
        ),
        signed_url=await storage_api.get_signed_url(db_document.storage_path),
        days_until=days_until,
        expiry_status=expiry_status,
    )
