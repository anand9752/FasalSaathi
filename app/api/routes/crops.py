from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.crop import Crop
from app.schemas.crop import CropRead, CropRecommendationItem, CropRecommendationRequest
from app.services.recommendation import build_recommendations


router = APIRouter()


@router.get("", response_model=list[CropRead])
def list_crops(db: Session = Depends(get_db)) -> list[Crop]:
    return list(db.scalars(select(Crop).order_by(Crop.name.asc())))


@router.post("/recommendation", response_model=list[CropRecommendationItem])
def recommend_crops(
    payload: CropRecommendationRequest, db: Session = Depends(get_db)
) -> list[CropRecommendationItem]:
    crops = list(db.scalars(select(Crop).order_by(Crop.name.asc())))
    return build_recommendations(crops, payload)
