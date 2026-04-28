from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Farm(Base):
    __tablename__ = "farms"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    location: Mapped[str] = mapped_column(String(255))
    area: Mapped[float] = mapped_column(Float)
    soil_type: Mapped[str] = mapped_column(String(100))
    irrigation_type: Mapped[str] = mapped_column(String(100))
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    owner = relationship("User", back_populates="farms")
    soil_tests = relationship("SoilTest", back_populates="farm", cascade="all, delete-orphan")
    crop_cycles = relationship("FarmCropCycle", back_populates="farm", cascade="all, delete-orphan")


class SoilTest(Base):
    __tablename__ = "soil_tests"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    farm_id: Mapped[int] = mapped_column(ForeignKey("farms.id", ondelete="CASCADE"), index=True)
    ph: Mapped[float] = mapped_column(Float)
    nitrogen: Mapped[float] = mapped_column(Float)
    phosphorus: Mapped[float] = mapped_column(Float)
    potassium: Mapped[float] = mapped_column(Float)
    organic_matter: Mapped[float] = mapped_column(Float)
    soil_moisture: Mapped[float] = mapped_column(Float, default=0)
    temperature: Mapped[float] = mapped_column(Float, default=0)
    test_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    farm = relationship("Farm", back_populates="soil_tests")

    @property
    def soil_ph(self) -> float:
        return self.ph
