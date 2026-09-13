import uuid
from datetime import date as dt_date
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.models.document import DocumentType

DocumentExpiryStatus = Literal["ok", "soon", "expired"]


class _DocumentDbFields(BaseModel):
    """ORM-backed document fields (excludes signed_url / computed labels)."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    vehicle_id: uuid.UUID
    document_type: DocumentType
    custom_label: str | None = None
    identifier: str | None = None
    expiry_date: dt_date | None = None
    notes: str | None = None


class DocumentResponse(_DocumentDbFields):
    """Response body for document endpoints."""
    display_label: str
    signed_url: str
    # Computed by the API — clients must not re-derive soon/expired thresholds.
    days_until: int | None = None
    expiry_status: DocumentExpiryStatus | None = None
