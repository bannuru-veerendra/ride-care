import enum
import uuid

from sqlalchemy import Column, Date, Enum, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.mixins import TimestampMixin


class DocumentType(str, enum.Enum):
    """Known certificate types; OTHER uses custom_label for free-text names."""
    INSURANCE = "insurance"
    DRIVING_LICENSE = "driving_license"
    REGISTRATION_CERTIFICATE = "registration_certificate"
    POLLUTION = "pollution"
    OTHER = "other"


class Document(Base, TimestampMixin):
    """Vehicle document vault entry (file in storage + certificate metadata)."""
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey("vehicles.id"), nullable=False)
    document_type = Column(Enum(DocumentType), nullable=False)
    storage_path = Column(String, nullable=False)
    # Free-text name when document_type is OTHER (e.g. Aadhaar, Form 20)
    custom_label = Column(String, nullable=True)
    # Certificate identity shown on the card (DL number, policy #, PUC #, …)
    identifier = Column(String, nullable=True)
    expiry_date = Column(Date, nullable=True)
    notes = Column(String, nullable=True)

    vehicle = relationship("Vehicle", back_populates="documents")

    __table_args__ = (
        Index("idx_documents_vehicle_id_created_at_id", "vehicle_id", "created_at", "id"),
        Index("idx_documents_vehicle_id_expiry_date", "vehicle_id", "expiry_date"),
    )
