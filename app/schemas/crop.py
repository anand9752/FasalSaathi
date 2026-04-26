from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import ORMModel


class CropRead(ORMModel):
    id: int
    name: str
    name_hindi: str
    scientific_name: str | None = None
    season: str
    duration: int
    water_requirement: float
    soil_compatibility: str
    estimated_yield_min: float
    estimated_yield_max: float
    estimated_profit: float
    investment_per_acre: float
    market_demand_level: str
    risk_level: str
    description: str
    created_at: datetime
    updated_at: datetime


class CropRecommendationRequest(BaseModel):
    soil_type: str
    season: str
    location: str
    irrigation_type: str | None = None
    search: str | None = None


class CropRecommendationItem(BaseModel):
    crop_id: int
    name: str
    name_hindi: str
    season: str
    score: float
    profit_margin: float
    estimated_yield_range: str
    water_requirement: str
    market_demand: str
    climate_suitability: str
    duration: str
    difficulty: str
    investment: float
    risk_level: str
    description: str

