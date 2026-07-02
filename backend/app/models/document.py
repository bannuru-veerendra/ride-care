import enum
import uuid

from sqlalchemy import Column, Date, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.mixins import TimestampMixin


class DocumentType(str, enum.Enum):
    """Document type enum"""
    INSURANCE = "insurance"
    DRIVING_LICENSE = "driving_license"
    REGISTRATION_CERTIFICATE = "registration_certificate"


class Document(Base, TimestampMixin):
    """Document model"""
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey("vehicles.id"), nullable=False, index=True)
    document_type = Column(Enum(DocumentType), nullable=False)
    storage_path = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    expiry_date = Column(Date, nullable=True)
    notes = Column(String, nullable=True)

    vehicle = relationship("Vehicle", back_populates="documents")
