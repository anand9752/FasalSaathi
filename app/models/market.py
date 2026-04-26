from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class MarketPrice(Base):
    __tablename__ = "market_prices"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    crop_id: Mapped[int] = mapped_column(ForeignKey("crops.id", ondelete="CASCADE"), index=True)
    market_name: Mapped[str] = mapped_column(String(255), index=True)
    price: Mapped[float] = mapped_column(Float)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    crop = relationship("Crop", back_populates="market_prices")

