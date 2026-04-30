"""
Weather service — fetches REAL data from OpenWeatherMap API.
Falls back to latest DB record when the API key is missing or the request fails.
Adds source ("live" | "cache" | "fallback") and is_stale metadata to every response.
"""

from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.weather import WeatherData
from app.schemas.weather import (
    WeatherCondition,
    WeatherCurrentResponse,
    WeatherForecastItem,
    WeatherForecastResponse,
    WeatherMain,
    WeatherWind,
)

# ── OpenWeatherMap endpoints ──────────────────────────────────────────────────
OWM_BASE = "https://api.openweathermap.org/data/2.5"
OWM_CURRENT = f"{OWM_BASE}/weather"
OWM_FORECAST = f"{OWM_BASE}/forecast"


# ── helpers ───────────────────────────────────────────────────────────────────

def _db_row_to_current(
    item: WeatherData,
    source: str = "fallback",
    is_stale: bool = True,
) -> WeatherCurrentResponse:
    return WeatherCurrentResponse(
        location=item.location,
        recorded_at=item.recorded_at,
        weather=[
            WeatherCondition(
                main=item.weather_main,
                description=item.weather_description,
                icon=item.weather_icon,
            )
        ],
        main=WeatherMain(
            temp=item.temperature,
            feels_like=item.temperature,
            humidity=item.humidity,
        ),
        wind=WeatherWind(speed=item.wind_speed),
        rainfall=item.rainfall,
        source=source,  # type: ignore[arg-type]
        is_stale=is_stale,
    )


def _save_weather_row(db: Session, location: str, data: dict) -> WeatherData:
    """Persist an OpenWeatherMap /weather JSON response to the DB."""
    rain = data.get("rain", {}).get("1h", 0.0)
    row = WeatherData(
        location=location,
        temperature=data["main"]["temp"],
        humidity=data["main"]["humidity"],
        rainfall=rain,
        wind_speed=data["wind"]["speed"],
        weather_main=data["weather"][0]["main"],
        weather_description=data["weather"][0]["description"],
        weather_icon=data["weather"][0]["icon"],
        recorded_at=datetime.now(timezone.utc),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _fetch_current_from_owm(
    location: str,
    lat: float | None = None,
    lon: float | None = None,
) -> dict | None:
    """Call OWM /weather and return raw JSON, or None on any error.

    When lat/lon are supplied they take precedence over the location string
    (OWM resolves coordinates more precisely than city-name queries).
    """
    api_key = settings.openweather_api_key
    if not api_key:
        return None
    try:
        if lat is not None and lon is not None:
            params = {
                "lat": lat,
                "lon": lon,
                "appid": api_key,
                "units": "metric",
                "lang": "en",
            }
        else:
            params = {
                "q": location,
                "appid": api_key,
                "units": "metric",
                "lang": "en",
            }
        resp = httpx.get(OWM_CURRENT, params=params, timeout=8)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def _fetch_forecast_from_owm(
    location: str,
    days: int,
    lat: float | None = None,
    lon: float | None = None,
) -> list[dict]:
    """Call OWM /forecast (3-hourly) and return one entry per day."""
    api_key = settings.openweather_api_key
    if not api_key:
        return []
    try:
        cnt = min(days * 8, 40)  # OWM gives 3-hourly; 8 per day, max 40
        if lat is not None and lon is not None:
            params = {
                "lat": lat,
                "lon": lon,
                "appid": api_key,
                "units": "metric",
                "cnt": cnt,
                "lang": "en",
            }
        else:
            params = {
                "q": location,
                "appid": api_key,
                "units": "metric",
                "cnt": cnt,
                "lang": "en",
            }
        resp = httpx.get(OWM_FORECAST, params=params, timeout=8)
        resp.raise_for_status()
        items = resp.json().get("list", [])
        # Take one reading per day (every 8th entry ≈ same time each day)
        daily = items[::8][:days] if len(items) >= 8 else items[:days]
        return daily
    except Exception:
        return []


# ── public interface ──────────────────────────────────────────────────────────

def get_current_weather(
    db: Session,
    location: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
) -> WeatherCurrentResponse:
    # Resolve a display location label and the coordinates to use for OWM
    if lat is not None and lon is not None:
        resolved_location = location or f"{lat},{lon}"
        owm_lat, owm_lon = lat, lon
    elif location:
        resolved_location = location
        owm_lat, owm_lon = None, None
    else:
        # No explicit coords or location — use configured defaults
        resolved_location = settings.weather_default_location
        owm_lat = settings.weather_default_lat
        owm_lon = settings.weather_default_lon

    # 1️⃣  Try real OWM API first
    owm_data = _fetch_current_from_owm(resolved_location, lat=owm_lat, lon=owm_lon)
    if owm_data:
        row = _save_weather_row(db, resolved_location, owm_data)
        return _db_row_to_current(row, source="live", is_stale=False)

    # 2️⃣  Fall back to the latest DB record for this location
    cached = db.scalars(
        select(WeatherData)
        .where(WeatherData.location == resolved_location)
        .order_by(WeatherData.recorded_at.desc())
    ).first()
    if cached:
        return _db_row_to_current(cached, source="cache", is_stale=True)

    # 3️⃣  Last resort: store a static placeholder so the UI never breaks
    fallback = WeatherData(
        location=resolved_location,
        temperature=29,
        humidity=60,
        rainfall=0,
        wind_speed=3.2,
        weather_main="Clear",
        weather_description="clear sky (offline)",
        weather_icon="01d",
        recorded_at=datetime.now(timezone.utc),
    )
    db.add(fallback)
    db.commit()
    db.refresh(fallback)
    return _db_row_to_current(fallback, source="fallback", is_stale=True)


def get_forecast(
    db: Session,
    location: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
    days: int = 3,
) -> WeatherForecastResponse:
    if lat is not None and lon is not None:
        resolved_location = location or f"{lat},{lon}"
        owm_lat, owm_lon = lat, lon
    elif location:
        resolved_location = location
        owm_lat, owm_lon = None, None
    else:
        resolved_location = settings.weather_default_location
        owm_lat = settings.weather_default_lat
        owm_lon = settings.weather_default_lon

    # 1️⃣  Try real OWM 5-day forecast
    owm_items = _fetch_forecast_from_owm(resolved_location, days, lat=owm_lat, lon=owm_lon)
    if owm_items:
        forecast = []
        for item in owm_items:
            rain = item.get("rain", {}).get("3h", 0.0)
            forecast.append(
                WeatherForecastItem(
                    recorded_at=datetime.fromtimestamp(item["dt"], tz=timezone.utc),
                    weather=[
                        WeatherCondition(
                            main=item["weather"][0]["main"],
                            description=item["weather"][0]["description"],
                            icon=item["weather"][0]["icon"],
                        )
                    ],
                    main=WeatherMain(
                        temp=item["main"]["temp"],
                        feels_like=item["main"]["feels_like"],
                        humidity=item["main"]["humidity"],
                    ),
                    wind=WeatherWind(speed=item["wind"]["speed"]),
                    rainfall=rain,
                )
            )
        return WeatherForecastResponse(
            location=resolved_location,
            forecast=forecast,
            source="live",
            is_stale=False,
        )

    # 2️⃣  Live forecast failed — return a single latest stale snapshot.
    #      Do NOT return multiple historical rows as fake future dates.
    latest = db.scalars(
        select(WeatherData)
        .where(WeatherData.location == resolved_location)
        .order_by(WeatherData.recorded_at.desc())
    ).first()

    if latest:
        return WeatherForecastResponse(
            location=resolved_location,
            forecast=[
                WeatherForecastItem(
                    recorded_at=latest.recorded_at,
                    weather=[
                        WeatherCondition(
                            main=latest.weather_main,
                            description=latest.weather_description,
                            icon=latest.weather_icon,
                        )
                    ],
                    main=WeatherMain(
                        temp=latest.temperature,
                        feels_like=latest.temperature,
                        humidity=latest.humidity,
                    ),
                    wind=WeatherWind(speed=latest.wind_speed),
                    rainfall=latest.rainfall,
                )
            ],
            source="cache",
            is_stale=True,
        )

    # 3️⃣  No data at all — call get_current_weather which handles the fallback
    current = get_current_weather(db, resolved_location)
    return WeatherForecastResponse(
        location=resolved_location,
        forecast=[
            WeatherForecastItem(
                recorded_at=current.recorded_at,
                weather=current.weather,
                main=current.main,
                wind=current.wind,
                rainfall=current.rainfall,
            )
        ],
        source=current.source,  # type: ignore[arg-type]
        is_stale=current.is_stale,
    )
