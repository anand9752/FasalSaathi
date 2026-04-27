from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class WeatherCondition(BaseModel):
    main: str
    description: str
    icon: str


class WeatherMain(BaseModel):
    temp: float
    feels_like: float
    humidity: float


class WeatherWind(BaseModel):
    speed: float


class WeatherCurrentResponse(BaseModel):
    location: str
    recorded_at: datetime
    weather: list[WeatherCondition]
    main: WeatherMain
    wind: WeatherWind
    rainfall: float = 0
    source: Literal["live", "cache", "fallback"] = "fallback"
    is_stale: bool = True


class WeatherForecastItem(BaseModel):
    recorded_at: datetime
    weather: list[WeatherCondition]
    main: WeatherMain
    wind: WeatherWind
    rainfall: float = 0


class WeatherForecastResponse(BaseModel):
    location: str
    forecast: list[WeatherForecastItem]
    source: Literal["live", "cache", "fallback"] = "fallback"
    is_stale: bool = True
