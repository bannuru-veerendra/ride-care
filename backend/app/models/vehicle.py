import uuid
from sqlalchemy import Column, String, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.extensions import Base
from app.models.mixins import TimestampMixin

class Vehicle(Base, TimestampMixin):
    """Vehicle model"""
    __tablename__ = "vehicles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    brand = Column(String, nullable=False)
    model = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    registration_number = Column(String, unique=True, index=True, nullable=False)
    current_odometer = Column(Integer, nullable=False)

    owner = relationship("User", back_populates="vehicles")
    fuel_logs = relationship("FuelLog", back_populates="vehicle", cascade="all, delete-orphan")
    service_logs = relationship("ServiceLog", back_populates="vehicle", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="vehicle", cascade="all, delete-orphan")
