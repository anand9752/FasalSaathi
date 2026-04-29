from datetime import datetime

from pydantic import BaseModel


class MarketPriceRead(BaseModel):
    id: str
    crop_id: int
    crop_name: str
    crop_name_hindi: str | None = None
    market_name: str
    price: float
    previous_price: float
    change: float
    change_percent: float
    date: datetime
    created_at: datetime
    state: str | None = None
    district: str | None = None
    variety: str | None = None
    min_price: float | None = None
    max_price: float | None = None
    modal_price: float | None = None
    source: str | None = None


class MarketPriceCurrent(MarketPriceRead):
    pass


class MarketTrendResponse(BaseModel):
    trend: str
    current_price: float
    average_price: float
    price_change: float
    forecast: str


class PriceAlertBase(BaseModel):
    commodity: str
    target_price: float
    condition: str  # 'above', 'below'


class PriceAlertCreate(PriceAlertBase):
    pass


class PriceAlertRead(PriceAlertBase):
    id: int
    user_id: int
    is_active: bool
    is_notified: bool
    created_at: datetime

    class Config:
        from_attributes = True
