from pydantic import BaseModel

from app.schemas.crop import CropRecommendationItem
from app.schemas.farm import CropCycleRead, FarmRead, SoilTestRead
from app.schemas.market import MarketPriceCurrent
from app.schemas.weather import WeatherCurrentResponse


class TodayPriority(BaseModel):
    title: str
    description: str
    recommended_time: str
    priority: str


class FarmVitals(BaseModel):
    soil_moisture: float
    soil_ph: float
    nitrogen: float
    phosphorus: float
    potassium: float
    temperature: float
    rainfall: float
    climate_summary: str


class YieldForecast(BaseModel):
    crop_name: str
    range_label: str
    progress_percent: float
    expected_harvest: str
    estimated_income_range: str


class DashboardOverview(BaseModel):
    farm: FarmRead | None = None
    active_crop: CropCycleRead | None = None
    latest_soil_test: SoilTestRead | None = None
    today_priority: TodayPriority | None = None
    farm_vitals: FarmVitals | None = None
    yield_forecast: YieldForecast | None = None
    weather: WeatherCurrentResponse | None = None
    market_alert: MarketPriceCurrent | None = None
    recommendation_preview: list[CropRecommendationItem] = []
