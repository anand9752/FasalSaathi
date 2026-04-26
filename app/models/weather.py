from datetime import datetime

from sqlalchemy import DateTime, Float, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class WeatherData(Base):
    __tablename__ = "weather_data"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    location: Mapped[str] = mapped_column(String(255), index=True)
    temperature: Mapped[float] = mapped_column(Float)
    humidity: Mapped[float] = mapped_column(Float)
    rainfall: Mapped[float] = mapped_column(Float, default=0)
    wind_speed: Mapped[float] = mapped_column(Float, default=0)
    weather_main: Mapped[str] = mapped_column(String(100), default="Clear")
    weather_description: Mapped[str] = mapped_column(String(255), default="clear sky")
    weather_icon: Mapped[str] = mapped_column(String(20), default="01d")
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

