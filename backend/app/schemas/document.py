import uuid
from datetime import date as dt_date

from pydantic import BaseModel, ConfigDict

from app.models.document import DocumentType


class _DocumentDbFields(BaseModel):
    """ORM-backed document fields (excludes signed_url)."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    vehicle_id: uuid.UUID
    document_type: DocumentType
    original_filename: str
    expiry_date: dt_date | None = None
    notes: str | None = None


class DocumentResponse(_DocumentDbFields):
    """Response body for document endpoints."""
    signed_url: str