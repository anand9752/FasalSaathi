from app.models.crop import Crop
from app.schemas.crop import CropRecommendationItem, CropRecommendationRequest


def _normalize(value: str) -> str:
    return value.strip().lower()


def _compatibility_score(crop: Crop, request: CropRecommendationRequest) -> float:
    score = 0
    if _normalize(request.season) == _normalize(crop.season):
        score += 35
    compat_soils = {_normalize(part) for part in crop.soil_compatibility.split(",") if part.strip()}
    if _normalize(request.soil_type) in compat_soils:
        score += 30
    if request.irrigation_type:
        irrigation = _normalize(request.irrigation_type)
        if irrigation in {"drip", "sprinkler"} and crop.water_requirement <= 60:
            score += 15
        elif irrigation in {"flood", "canal"} and crop.water_requirement >= 40:
            score += 12
        else:
            score += 8
    else:
        score += 10

    demand_bonus = {"high": 12, "medium": 8, "low": 4}.get(crop.market_demand_level.lower(), 5)
    risk_penalty = {"low": 8, "medium": 4, "high": 0}.get(crop.risk_level.lower(), 2)
    score += demand_bonus + risk_penalty
    return float(min(score, 100))


def build_recommendations(
    crops: list[Crop], request: CropRecommendationRequest
) -> list[CropRecommendationItem]:
    recommendations: list[CropRecommendationItem] = []
    for crop in crops:
        if request.search and request.search.lower() not in crop.name.lower() and request.search not in crop.name_hindi:
            continue
        score = _compatibility_score(crop, request)
        water_label = (
            "low" if crop.water_requirement < 40 else "medium" if crop.water_requirement < 65 else "high"
        )
        suitability = "excellent" if score >= 80 else "good" if score >= 60 else "fair"
        difficulty = "easy" if crop.risk_level == "low" else "medium" if crop.risk_level == "medium" else "hard"
        recommendations.append(
            CropRecommendationItem(
                crop_id=crop.id,
                name=crop.name,
                name_hindi=crop.name_hindi,
                season=crop.season,
                score=round(score, 2),
                profit_margin=crop.estimated_profit,
                estimated_yield_range=f"{crop.estimated_yield_min:.0f}-{crop.estimated_yield_max:.0f} quintal/acre",
                water_requirement=water_label,
                market_demand=crop.market_demand_level,
                climate_suitability=suitability,
                duration=f"{crop.duration} days",
                difficulty=difficulty,
                investment=crop.investment_per_acre,
                risk_level=crop.risk_level,
                description=crop.description,
            )
        )
    return sorted(recommendations, key=lambda item: (item.score, item.profit_margin), reverse=True)

