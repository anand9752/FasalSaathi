from dataclasses import asdict

from sqlalchemy.orm import Session

from app.schemas.crop import CropDetailResponse, CropRecommendationItem, CropRecommendationRequest
from app.services.crop_catalog import CROP_RULES, CropRule, get_crop_rule
from app.services.gemini import generate_structured_json
from app.services.weather import get_current_weather


def _within_range(value: float, lower: float, upper: float) -> bool:
    return lower <= value <= upper


def _range_score(value: float, lower: float, upper: float) -> float:
    if _within_range(value, lower, upper):
        return 1.0
    distance = lower - value if value < lower else value - upper
    span = max(upper - lower, 1.0)
    return max(0.0, 1.0 - (distance / span))


def _water_label_from_moisture(soil_moisture: float) -> str:
    if soil_moisture < 35:
        return "Low"
    if soil_moisture < 65:
        return "Medium"
    return "High"


def _climate_summary(payload: CropRecommendationRequest, weather_context: dict[str, float | str | None]) -> str:
    parts = [
        f"Soil pH {payload.soil_ph:.1f}",
        f"soil moisture {payload.soil_moisture:.0f}%",
        f"temperature {payload.temperature:.1f}C",
        f"rainfall {payload.rainfall:.1f} mm",
    ]
    live_temp = weather_context.get("live_temperature")
    live_rainfall = weather_context.get("live_rainfall")
    if isinstance(live_temp, (int, float)):
        parts.append(f"live weather temperature {live_temp:.1f}C")
    if isinstance(live_rainfall, (int, float)):
        parts.append(f"live rainfall {live_rainfall:.1f} mm")
    if weather_context.get("weather_description"):
        parts.append(f"weather {weather_context['weather_description']}")
    return ", ".join(parts)


def _score_crop(crop: CropRule, payload: CropRecommendationRequest) -> tuple[bool, float]:
    component_scores = [
        _range_score(payload.soil_ph, crop.soil_ph_min, crop.soil_ph_max),
        _range_score(payload.nitrogen, crop.nitrogen_min, crop.nitrogen_max),
        _range_score(payload.phosphorus, crop.phosphorus_min, crop.phosphorus_max),
        _range_score(payload.potassium, crop.potassium_min, crop.potassium_max),
        _range_score(payload.soil_moisture, crop.soil_moisture_min, crop.soil_moisture_max),
        _range_score(payload.rainfall, crop.rainfall_min, crop.rainfall_max),
        _range_score(payload.temperature, crop.temperature_min, crop.temperature_max),
    ]
    exact_matches = sum(score >= 0.999 for score in component_scores)
    is_eligible = exact_matches >= 4 and component_scores[0] >= 0.999
    total_score = round((sum(component_scores) / len(component_scores)) * 100, 2)
    return is_eligible, total_score


def _fallback_item(crop: CropRule, score: float, climate_summary: str) -> CropRecommendationItem:
    if score >= 85:
        climate_suitability = "Excellent fit"
    elif score >= 70:
        climate_suitability = "Good fit"
    elif score >= 55:
        climate_suitability = "Moderate fit"
    else:
        climate_suitability = "Borderline fit"

    return CropRecommendationItem(
        crop_id=crop.crop_id,
        name=crop.name,
        name_hindi=crop.name_hindi,
        season=crop.season,
        score=score,
        profit_margin=crop.default_profit_margin,
        estimated_yield_range=crop.default_yield_range,
        water_requirement=crop.base_water_requirement,
        market_demand=crop.base_market_demand,
        climate_suitability=climate_suitability,
        duration=crop.base_duration,
        investment=crop.default_investment,
        risk_level=crop.default_risk_level,
        description=f"{crop.default_description} Farm context: {climate_summary}.",
    )


def _recommendation_schema() -> dict:
    return {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "name_hindi": {"type": "string"},
                "profit_margin": {"type": "number"},
                "estimated_yield_range": {"type": "string"},
                "water_requirement": {"type": "string"},
                "market_demand": {"type": "string"},
                "climate_suitability": {"type": "string"},
                "duration": {"type": "string"},
                "investment": {"type": "number"},
                "risk_level": {"type": "string"},
                "description": {"type": "string"},
            },
            "required": [
                "name",
                "name_hindi",
                "profit_margin",
                "estimated_yield_range",
                "water_requirement",
                "market_demand",
                "climate_suitability",
                "duration",
                "investment",
                "risk_level",
                "description",
            ],
        },
    }


def _crop_detail_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "crop_name": {"type": "string"},
            "crop_name_hindi": {"type": "string"},
            "overview": {"type": "string"},
            "land_preparation": {"type": "array", "items": {"type": "string"}},
            "sowing_time": {"type": "array", "items": {"type": "string"}},
            "irrigation_schedule": {"type": "array", "items": {"type": "string"}},
            "fertilizers": {"type": "array", "items": {"type": "string"}},
            "pesticides": {"type": "array", "items": {"type": "string"}},
            "harvesting": {"type": "array", "items": {"type": "string"}},
        },
        "required": [
            "crop_name",
            "crop_name_hindi",
            "overview",
            "land_preparation",
            "sowing_time",
            "irrigation_schedule",
            "fertilizers",
            "pesticides",
            "harvesting",
        ],
    }


def _build_weather_context(db: Session, location: str) -> dict[str, float | str | None]:
    weather = get_current_weather(db, location=location)
    return {
        "live_temperature": weather.main.temp,
        "live_rainfall": weather.rainfall,
        "weather_description": weather.weather[0].description if weather.weather else None,
    }


def recommend_crops_dynamic(db: Session, payload: CropRecommendationRequest) -> list[CropRecommendationItem]:
    weather_context = _build_weather_context(db, payload.location)
    eligible: list[tuple[CropRule, float]] = []
    fallback_ranked: list[tuple[CropRule, float]] = []

    for crop in CROP_RULES:
        is_eligible, score = _score_crop(crop, payload)
        fallback_ranked.append((crop, score))
        if is_eligible:
            eligible.append((crop, score))

    ranked = eligible or fallback_ranked
    top_candidates = sorted(ranked, key=lambda item: item[1], reverse=True)[:5]

    climate_summary = _climate_summary(payload, weather_context)
    fallback_items = [_fallback_item(crop, score, climate_summary) for crop, score in top_candidates]

    prompt = (
        "Based on the following farm conditions, suggest top 5 crops with detailed farming insights. "
        "Use the candidate crop list exactly as given and return concise, practical results for Indian farmers.\n\n"
        f"Farm conditions: {payload.model_dump_json()}\n"
        f"Live weather context: {weather_context}\n"
        f"Candidate crops: {[asdict(crop) for crop, _score in top_candidates]}\n\n"
        "Return only JSON."
    )
    structured = generate_structured_json(prompt, _recommendation_schema())
    if not isinstance(structured, list):
        return fallback_items

    enriched_by_name = {
        str(item.get("name", "")).strip().lower(): item
        for item in structured
        if isinstance(item, dict) and item.get("name")
    }

    results: list[CropRecommendationItem] = []
    for fallback in fallback_items:
        enriched = enriched_by_name.get(fallback.name.lower())
        if not enriched:
            results.append(fallback)
            continue

        results.append(
            CropRecommendationItem(
                crop_id=fallback.crop_id,
                name=fallback.name,
                name_hindi=str(enriched.get("name_hindi") or fallback.name_hindi),
                season=fallback.season,
                score=fallback.score,
                profit_margin=float(enriched.get("profit_margin", fallback.profit_margin)),
                estimated_yield_range=str(enriched.get("estimated_yield_range") or fallback.estimated_yield_range),
                water_requirement=str(enriched.get("water_requirement") or fallback.water_requirement),
                market_demand=str(enriched.get("market_demand") or fallback.market_demand),
                climate_suitability=str(enriched.get("climate_suitability") or fallback.climate_suitability),
                duration=str(enriched.get("duration") or fallback.duration),
                investment=float(enriched.get("investment", fallback.investment)),
                risk_level=str(enriched.get("risk_level") or fallback.risk_level),
                description=str(enriched.get("description") or fallback.description),
            )
        )

    return results


def get_crop_detail_guide(crop_name: str) -> CropDetailResponse:
    crop = get_crop_rule(crop_name)
    if not crop:
        raise ValueError("Crop not found")

    prompt = (
        "Create a practical farming guide for an Indian farmer. "
        "Cover land preparation, sowing time, irrigation schedule, fertilizers, pesticides, and harvesting. "
        f"Crop profile: {asdict(crop)}. Return only JSON."
    )
    structured = generate_structured_json(prompt, _crop_detail_schema())
    if isinstance(structured, dict):
        try:
            return CropDetailResponse(**structured)
        except Exception:
            pass

    return CropDetailResponse(
        crop_name=crop.name,
        crop_name_hindi=crop.name_hindi,
        overview=crop.default_description,
        land_preparation=[
            "Prepare a fine, weed-free seedbed with one deep ploughing followed by 2 light harrowings.",
            "Add well-decomposed organic manure before final land preparation.",
        ],
        sowing_time=[
            f"Target the normal {crop.season.lower()} sowing window for your district.",
            "Use healthy, treated seed and maintain proper spacing for airflow and sunlight.",
        ],
        irrigation_schedule=[
            f"Keep irrigation aligned with the crop's {crop.base_water_requirement.lower()} water demand.",
            "Avoid waterlogging and irrigate more carefully during germination, flowering, and grain or pod filling stages.",
        ],
        fertilizers=[
            "Apply nutrients according to soil test results instead of blanket doses.",
            "Split nitrogen applications where suitable to improve uptake and reduce losses.",
        ],
        pesticides=[
            "Scout the field weekly and use integrated pest management before chemical spraying.",
            "Choose pesticides only after identifying the pest or disease pressure correctly.",
        ],
        harvesting=[
            "Harvest at physiological maturity to reduce shattering and storage losses.",
            "Dry produce properly before storage or market transport.",
        ],
    )
