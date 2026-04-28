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
    soil_ph: float
    nitrogen: float
    phosphorus: float
    potassium: float
    soil_moisture: float
    temperature: float
    rainfall: float
    location: str


class CropRecommendationItem(BaseModel):
    crop_id: int
    name: str
    name_hindi: str
    season: str | None = None
    score: float | None = None
    profit_margin: float
    estimated_yield_range: str
    water_requirement: str
    market_demand: str
    climate_suitability: str
    duration: str
    investment: float
    risk_level: str
    description: str


class CropDetailResponse(BaseModel):
    crop_name: str
    crop_name_hindi: str
    overview: str
    land_preparation: list[str]
    sowing_time: list[str]
    irrigation_schedule: list[str]
    fertilizers: list[str]
    pesticides: list[str]
    harvesting: list[str]
