import uuid
from datetime import date as dt_date

from sqlalchemy import Column, Date, ForeignKey, Integer, String, Text, Float
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.mixins import TimestampMixin


class ServiceLog(Base, TimestampMixin):
    """Service log model"""
    __tablename__ = "service_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey("vehicles.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    odometer = Column(Integer, nullable=False)
    service_center = Column(String, nullable=True)
    total_cost = Column(Float, nullable=False, default=0)
    services_done = Column(ARRAY(String), nullable=False)
    next_service_date = Column(Date, nullable=True)
    next_service_odometer = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)

    vehicle = relationship("Vehicle", back_populates="service_logs")