from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.market import MarketPriceCurrent, MarketPriceRead, MarketTrendResponse
from app.services.market import get_current_prices, get_markets, get_market_trend, get_price_history


router = APIRouter()


@router.get("/prices/current", response_model=list[MarketPriceCurrent])
def current_prices(
    state: str | None = Query(default=None),
    market: str | None = Query(default=None),
    commodity: str | None = Query(default=None),
    crop_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[MarketPriceCurrent]:
    return get_current_prices(
        db,
        state=state,
        market=market,
        commodity=commodity,
        crop_id=crop_id,
    )


@router.get("/prices/history/{crop_id}", response_model=list[MarketPriceRead])
def price_history(crop_id: int, days: int = Query(default=30, ge=1), db: Session = Depends(get_db)):
    return get_price_history(db, crop_id, days)


@router.get("/markets", response_model=list[str])
def markets(db: Session = Depends(get_db)) -> list[str]:
    return get_markets(db)


@router.get("/trends/{crop_id}", response_model=MarketTrendResponse)
def market_trends(crop_id: int, db: Session = Depends(get_db)) -> MarketTrendResponse:
    return get_market_trend(db, crop_id)
