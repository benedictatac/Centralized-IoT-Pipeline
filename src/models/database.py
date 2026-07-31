from datetime import datetime
import uuid

from sqlalchemy import ForeignKey, String, Float, DateTime, func, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class DeviceDB(Base):
    __tablename__ = "devices"

    device_id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4, server_default=text('gen_random_uuid()')
    )
    device_name: Mapped[str] = mapped_column(String, nullable=False)
    device_type: Mapped[str] = mapped_column(String, nullable=False)
    
    # Defaults handled both in-app and at database level via server_default
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # One-to-Many Relationship to Readings
    readings: Mapped[list["Reading"]] = relationship(
        back_populates="device", cascade="all, delete-orphan" # want all data deleted on it if device is deleted
    )


class Reading(Base):
    __tablename__ = "readings"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4, server_default=text('gen_random_uuid()')
    )
    device_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("devices.device_id"), nullable=False
    )
    metric: Mapped[str] = mapped_column(String, nullable=False)
    unit: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # Many-to-One Relationship back to Device
    device: Mapped["DeviceDB"] = relationship(back_populates="readings")