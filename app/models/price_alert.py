from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

class PriceAlert(Base):
    __tablename__ = "price_alerts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    commodity: Mapped[str] = mapped_column(String(255), index=True)
    target_price: Mapped[float] = mapped_column(Float)
    condition: Mapped[str] = mapped_column(String(20))  # 'above', 'below'
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_notified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", backref="price_alerts")
