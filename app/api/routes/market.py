from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.market import MarketPriceCurrent, MarketPriceRead, MarketTrendResponse, PriceAlertCreate, PriceAlertRead
from app.services.market import get_current_prices, get_markets, get_market_trend, get_price_history, create_price_alert, get_user_price_alerts, delete_price_alert
from app.api.deps import get_current_active_user
from app.models.user import User


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


@router.post("/alerts", response_model=PriceAlertRead)
def create_alert(
    alert_in: PriceAlertCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> PriceAlertRead:
    return create_price_alert(db, current_user.id, alert_in)


@router.get("/alerts", response_model=list[PriceAlertRead])
def list_alerts(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> list[PriceAlertRead]:
    return get_user_price_alerts(db, current_user.id)


@router.delete("/alerts/{alert_id}")
def remove_alert(
    alert_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if not delete_price_alert(db, current_user.id, alert_id):
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"status": "deleted"}
