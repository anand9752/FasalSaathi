from datetime import date, datetime

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


class ManagedCropBase(BaseModel):
    farm_id: int
    name: str
    name_hindi: str
    crop_type: str
    season: str = ""
    duration: int
    area: float
    estimated_cost: float
    estimated_profit: float
    expected_yield: float | None = None
    risk_level: str
    status: str = "planned"
    sowing_date: date | None = None
    expected_harvest_date: date | None = None
    actual_harvest_date: date | None = None
    variety: str | None = None
    water_requirement: str = ""
    soil_preference: str = ""
    description: str = ""
    notes: str = ""


class ManagedCropCreate(ManagedCropBase):
    pass


class ManagedCropUpdate(BaseModel):
    farm_id: int | None = None
    name: str | None = None
    name_hindi: str | None = None
    crop_type: str | None = None
    season: str | None = None
    duration: int | None = None
    area: float | None = None
    estimated_cost: float | None = None
    estimated_profit: float | None = None
    expected_yield: float | None = None
    risk_level: str | None = None
    status: str | None = None
    sowing_date: date | None = None
    expected_harvest_date: date | None = None
    actual_harvest_date: date | None = None
    variety: str | None = None
    water_requirement: str | None = None
    soil_preference: str | None = None
    description: str | None = None
    notes: str | None = None


class ManagedCropRead(ORMModel):
    id: int
    farm_id: int
    farm_name: str
    name: str
    name_hindi: str
    crop_type: str
    season: str
    duration: int
    area: float
    estimated_cost: float
    estimated_profit: float
    expected_yield: float | None = None
    risk_level: str
    status: str
    sowing_date: date | None = None
    expected_harvest_date: date | None = None
    actual_harvest_date: date | None = None
    variety: str | None = None
    water_requirement: str
    soil_preference: str
    description: str
    notes: str
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
