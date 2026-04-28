from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.crop import CropDetailResponse, CropRecommendationItem, CropRecommendationRequest
from app.services.crop_recommendation import get_crop_detail_guide, recommend_crops_dynamic


router = APIRouter()


@router.post("/crop-recommendation", response_model=list[CropRecommendationItem])
def crop_recommendation(
    payload: CropRecommendationRequest,
    db: Session = Depends(get_db),
) -> list[CropRecommendationItem]:
    return recommend_crops_dynamic(db, payload)


@router.get("/crop-detail", response_model=CropDetailResponse)
def crop_detail(crop_name: str = Query(..., min_length=2)) -> CropDetailResponse:
    try:
        return get_crop_detail_guide(crop_name)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
