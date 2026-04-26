from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.market import MarketPrice
from app.schemas.market import MarketPriceCurrent, MarketTrendResponse


def get_current_prices(
    db: Session, market: str | None = None, crop_id: int | None = None
) -> list[MarketPriceCurrent]:
    prices = list(
        db.scalars(
            select(MarketPrice)
            .options(joinedload(MarketPrice.crop))
            .order_by(MarketPrice.crop_id.asc(), MarketPrice.date.desc())
        )
    )
    grouped: dict[tuple[int, str], list[MarketPrice]] = defaultdict(list)
    for price in prices:
        if market and price.market_name != market:
            continue
        if crop_id and price.crop_id != crop_id:
            continue
        grouped[(price.crop_id, price.market_name)].append(price)

    current_prices: list[MarketPriceCurrent] = []
    for history in grouped.values():
        current = history[0]
        previous = history[1] if len(history) > 1 else history[0]
        delta = current.price - previous.price
        delta_pct = (delta / previous.price * 100) if previous.price else 0
        current_prices.append(
            MarketPriceCurrent(
                id=current.id,
                crop_id=current.crop_id,
                crop_name=current.crop.name,
                crop_name_hindi=current.crop.name_hindi,
                market_name=current.market_name,
                price=current.price,
                previous_price=previous.price,
                change=round(delta, 2),
                change_percent=round(delta_pct, 2),
                date=current.date,
            )
        )
    return sorted(current_prices, key=lambda item: item.change_percent, reverse=True)


def get_price_history(db: Session, crop_id: int, days: int = 30) -> list[MarketPrice]:
    return list(
        db.scalars(
            select(MarketPrice)
            .where(MarketPrice.crop_id == crop_id)
            .order_by(MarketPrice.date.desc())
            .limit(max(days, 1))
        )
    )


def get_markets(db: Session) -> list[str]:
    rows = db.scalars(select(MarketPrice.market_name).distinct().order_by(MarketPrice.market_name.asc()))
    return list(rows)


def get_market_trend(db: Session, crop_id: int) -> MarketTrendResponse:
    history = get_price_history(db, crop_id, days=7)
    if not history:
        return MarketTrendResponse(
            trend="stable",
            current_price=0,
            average_price=0,
            price_change=0,
            forecast="No recent market data available.",
        )
    current = history[0].price
    average = sum(item.price for item in history) / len(history)
    oldest = history[-1].price
    delta = round(current - oldest, 2)
    trend = "up" if delta > 0 else "down" if delta < 0 else "stable"
    forecast = (
        "Prices are strengthening; consider monitoring for a favorable selling window."
        if trend == "up"
        else "Prices are softening; avoid distress selling if storage is available."
        if trend == "down"
        else "Prices are stable over the recent period."
    )
    return MarketTrendResponse(
        trend=trend,
        current_price=current,
        average_price=round(average, 2),
        price_change=delta,
        forecast=forecast,
    )

