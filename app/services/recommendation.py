from app.schemas.crop import CropRecommendationItem, CropRecommendationRequest
from app.services.crop_catalog import CROP_RULES
from app.services.crop_recommendation import _climate_summary, _fallback_item, _score_crop


def build_recommendations(
    crops: list[object], request: CropRecommendationRequest
) -> list[CropRecommendationItem]:
    del crops
    climate_summary = _climate_summary(request, {})
    ranked = sorted(
        ((_fallback_item(crop, _score_crop(crop, request)[1], climate_summary)) for crop in CROP_RULES),
        key=lambda item: (item.score or 0, item.profit_margin),
        reverse=True,
    )
    return ranked
