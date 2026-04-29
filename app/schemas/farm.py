from datetime import date, datetime

from pydantic import BaseModel

from app.schemas.common import ORMModel
from app.schemas.crop import ManagedCropRead


class SoilTestRead(ORMModel):
    id: int
    farm_id: int
    soil_ph: float
    nitrogen: float
    phosphorus: float
    potassium: float
    organic_matter: float
    soil_moisture: float
    temperature: float
    test_date: datetime
    created_at: datetime
    updated_at: datetime


class SoilTestCreate(BaseModel):
    farm_id: int
    soil_ph: float
    nitrogen: float
    phosphorus: float
    potassium: float
    soil_moisture: float
    temperature: float


class CropCycleRead(BaseModel):
    id: int
    crop_id: int
    crop_name: str
    crop_name_hindi: str
    season: str
    year: int
    sowing_date: date | None = None
    expected_harvest_date: date | None = None
    area: float
    status: str
    yield_achieved: float | None = None
    profit_loss: float | None = None


class FarmBase(BaseModel):
    name: str
    location: str
    area: float
    soil_type: str
    irrigation_type: str


class FarmCreate(FarmBase):
    initial_crop_id: int | None = None
    initial_crop_season: str | None = None
    initial_crop_year: int | None = None


class FarmUpdate(BaseModel):
    name: str | None = None
    location: str | None = None
    area: float | None = None
    soil_type: str | None = None
    irrigation_type: str | None = None


class FarmRead(ORMModel):
    id: int
    name: str
    location: str
    area: float
    soil_type: str
    irrigation_type: str
    owner_id: int
    created_at: datetime
    updated_at: datetime
    soil_tests: list[SoilTestRead] = []
    crop_cycles: list[CropCycleRead] = []
    managed_crops: list[ManagedCropRead] = []
