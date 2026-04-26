from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import ORMModel


class MarketPriceRead(ORMModel):
    id: int
    crop_id: int
    market_name: str
    price: float
    date: datetime
    created_at: datetime


class MarketPriceCurrent(BaseModel):
    id: int
    crop_id: int
    crop_name: str
    crop_name_hindi: str
    market_name: str
    price: float
    previous_price: float
    change: float
    change_percent: float
    date: datetime


class MarketTrendResponse(BaseModel):
    trend: str
    current_price: float
    average_price: float
    price_change: float
    forecast: str

