import uuid

from sqlalchemy import Column, Date, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.mixins import TimestampMixin


class FuelLog(Base, TimestampMixin):
    """Fuel log model"""
    __tablename__ = "fuel_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey("vehicles.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    odometer = Column(Integer, nullable=False)
    liters = Column(Float, nullable=False)
    price_per_liter = Column(Float, nullable=False)
    total_cost = Column(Float, nullable=False)
    mileage = Column(Integer, nullable=True)
    notes = Column(String, nullable=True)

    vehicle = relationship("Vehicle", back_populates="fuel_logs")
