from datetime import UTC, datetime
import hashlib

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.schemas.market import MarketPriceCurrent, MarketPriceRead, MarketTrendResponse


def _coerce_price(value: str | int | float | None) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_arrival_date(value: str | None) -> datetime:
    if value:
        for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(value, fmt).replace(tzinfo=UTC)
            except ValueError:
                continue
    return datetime.now(UTC)


def _hash_to_int(value: str) -> int:
    digest = hashlib.md5(value.strip().lower().encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def _build_record_id(record: dict) -> str:
    fields = [
        str(record.get("state", "")).strip().lower().replace(" ", "-"),
        str(record.get("district", "")).strip().lower().replace(" ", "-"),
        str(record.get("market", "")).strip().lower().replace(" ", "-"),
        str(record.get("commodity", "")).strip().lower().replace(" ", "-"),
        str(record.get("variety", "")).strip().lower().replace(" ", "-"),
        str(record.get("arrival_date", "")).strip().replace("/", "-"),
    ]
    return "-".join(part or "na" for part in fields)


def _market_resource_url() -> str:
    base = settings.data_gov_base_url.rstrip("/")
    return f"{base}/{settings.data_gov_market_resource_id}"


def _fetch_market_records(
    state: str | None = None,
    market: str | None = None,
    commodity: str | None = None,
) -> list[dict]:
    api_key = settings.data_gov_api_key
    if not api_key:
        return []

    has_filters = any((state, market, commodity))
    limit = settings.data_gov_filtered_limit if has_filters else settings.data_gov_default_limit
    max_pages = settings.data_gov_max_filtered_pages if has_filters else 1

    records: list[dict] = []
    offset = 0

    for _ in range(max_pages):
        params: dict[str, str | int] = {
            "api-key": api_key,
            "format": "json",
            "limit": limit,
            "offset": offset,
        }
        if state:
            params["filters[state]"] = state
        if market:
            params["filters[market]"] = market
        if commodity:
            params["filters[commodity]"] = commodity

        try:
            response = httpx.get(
                _market_resource_url(),
                params=params,
                timeout=settings.data_gov_timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
        except Exception:
            return []

        page_records = payload.get("records", [])
        if not page_records:
            break

        records.extend(page_records)

        try:
            total_records = int(payload.get("total", len(records)))
        except (TypeError, ValueError):
            total_records = len(records)

        offset += limit
        if len(records) >= total_records:
            break

    return records


def _normalize_market_record(record: dict) -> MarketPriceCurrent | None:
    modal_price = _coerce_price(record.get("modal_price"))
    if modal_price is None:
        return None

    commodity = str(record.get("commodity", "")).strip()
    market_name = str(record.get("market", "")).strip()
    if not commodity or not market_name:
        return None

    arrival_date = _parse_arrival_date(record.get("arrival_date"))
    crop_id = _hash_to_int(commodity)

    return MarketPriceCurrent(
        id=_build_record_id(record),
        crop_id=crop_id,
        crop_name=commodity,
        crop_name_hindi=None,
        market_name=market_name,
        price=modal_price,
        previous_price=modal_price,
        change=0.0,
        change_percent=0.0,
        date=arrival_date,
        created_at=arrival_date,
        state=str(record.get("state", "")).strip() or None,
        district=str(record.get("district", "")).strip() or None,
        variety=str(record.get("variety", "")).strip() or None,
        min_price=_coerce_price(record.get("min_price")),
        max_price=_coerce_price(record.get("max_price")),
        modal_price=modal_price,
        source="live",
    )


def get_current_prices(
    db: Session,
    state: str | None = None,
    market: str | None = None,
    commodity: str | None = None,
    crop_id: int | None = None,
) -> list[MarketPriceCurrent]:
    del db

    current_prices = [
        item
        for item in (_normalize_market_record(record) for record in _fetch_market_records(state=state, market=market, commodity=commodity))
        if item is not None
    ]

    if crop_id is not None:
        current_prices = [item for item in current_prices if item.crop_id == crop_id]

    return sorted(
        current_prices,
        key=lambda item: (item.price, item.crop_name.lower(), item.market_name.lower()),
        reverse=True,
    )


def get_price_history(db: Session, crop_id: int, days: int = 30) -> list[MarketPriceRead]:
    del days
    return [MarketPriceRead(**item.model_dump()) for item in get_current_prices(db, crop_id=crop_id)]


def get_markets(db: Session) -> list[str]:
    del db
    markets = {
        market_name
        for market_name in (str(record.get("market", "")).strip() for record in _fetch_market_records())
        if market_name
    }
    return sorted(markets)


def get_market_trend(db: Session, crop_id: int) -> MarketTrendResponse:
    history = get_price_history(db, crop_id, days=7)
    if not history:
        return MarketTrendResponse(
            trend="stable",
            current_price=0,
            average_price=0,
            price_change=0,
            forecast="No live market data is available for this commodity right now.",
        )

    current = history[0].price
    average = sum(item.price for item in history) / len(history)
    return MarketTrendResponse(
        trend="stable",
        current_price=current,
        average_price=round(average, 2),
        price_change=0,
        forecast="Live mandi feed provides current daily prices only, so historical movement is unavailable.",
    )
