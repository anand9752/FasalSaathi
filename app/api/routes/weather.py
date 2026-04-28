from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.weather import WeatherCurrentResponse, WeatherForecastResponse
from app.services.weather import get_current_weather, get_forecast


router = APIRouter()


@router.get("/current", response_model=WeatherCurrentResponse)
def current_weather(
    lat: float | None = Query(default=None),
    lon: float | None = Query(default=None),
    location: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> WeatherCurrentResponse:
    return get_current_weather(db, location=location, lat=lat, lon=lon)


@router.get("/forecast", response_model=WeatherForecastResponse)
def weather_forecast(
    days: int = Query(default=3, ge=1, le=10),
    lat: float | None = Query(default=None),
    lon: float | None = Query(default=None),
    location: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> WeatherForecastResponse:
    return get_forecast(db, location=location, lat=lat, lon=lon, days=days)
