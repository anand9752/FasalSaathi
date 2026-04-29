from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Crop(Base):
    __tablename__ = "crops"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name_hindi: Mapped[str] = mapped_column(String(255))
    scientific_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    season: Mapped[str] = mapped_column(String(50))
    duration: Mapped[int] = mapped_column(Integer)
    water_requirement: Mapped[float] = mapped_column(Float, default=0)
    soil_compatibility: Mapped[str] = mapped_column(String(255), default="")
    estimated_yield_min: Mapped[float] = mapped_column(Float, default=0)
    estimated_yield_max: Mapped[float] = mapped_column(Float, default=0)
    estimated_profit: Mapped[float] = mapped_column(Float, default=0)
    investment_per_acre: Mapped[float] = mapped_column(Float, default=0)
    market_demand_level: Mapped[str] = mapped_column(String(20), default="medium")
    risk_level: Mapped[str] = mapped_column(String(20), default="medium")
    description: Mapped[str] = mapped_column(String(500), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    farm_cycles = relationship("FarmCropCycle", back_populates="crop")
    market_prices = relationship("MarketPrice", back_populates="crop")


class FarmCropCycle(Base):
    __tablename__ = "farm_crop_cycles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    farm_id: Mapped[int] = mapped_column(ForeignKey("farms.id", ondelete="CASCADE"), index=True)
    crop_id: Mapped[int] = mapped_column(ForeignKey("crops.id", ondelete="CASCADE"), index=True)
    season: Mapped[str] = mapped_column(String(50))
    year: Mapped[int] = mapped_column(Integer)
    sowing_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expected_harvest_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    area: Mapped[float] = mapped_column(Float, default=0)
    status: Mapped[str] = mapped_column(String(30), default="planned")
    yield_achieved: Mapped[float | None] = mapped_column(Float, nullable=True)
    profit_loss: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    farm = relationship("Farm", back_populates="crop_cycles")
    crop = relationship("Crop", back_populates="farm_cycles")


class ManagedCrop(Base):
    __tablename__ = "managed_crops"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    farm_id: Mapped[int] = mapped_column(ForeignKey("farms.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    name_hindi: Mapped[str] = mapped_column(String(255))
    crop_type: Mapped[str] = mapped_column(String(100), default="field")
    season: Mapped[str] = mapped_column(String(50), default="")
    duration: Mapped[int] = mapped_column(Integer, default=0)
    area: Mapped[float] = mapped_column(Float, default=0)
    estimated_cost: Mapped[float] = mapped_column(Float, default=0)
    estimated_profit: Mapped[float] = mapped_column(Float, default=0)
    expected_yield: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_level: Mapped[str] = mapped_column(String(20), default="medium")
    status: Mapped[str] = mapped_column(String(30), default="planned")
    sowing_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expected_harvest_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    actual_harvest_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    variety: Mapped[str | None] = mapped_column(String(255), nullable=True)
    water_requirement: Mapped[str] = mapped_column(String(255), default="")
    soil_preference: Mapped[str] = mapped_column(String(255), default="")
    description: Mapped[str] = mapped_column(String(1000), default="")
    notes: Mapped[str] = mapped_column(String(1000), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    farm = relationship("Farm", back_populates="managed_crops")
