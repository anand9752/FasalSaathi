from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.farm import SoilTestCreate, SoilTestRead
from app.services.soil_tests import create_soil_test, get_latest_soil_test


router = APIRouter()


@router.post("", response_model=SoilTestRead, status_code=status.HTTP_201_CREATED)
def create_soil_test_entry(
    payload: SoilTestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SoilTestRead:
    try:
        return SoilTestRead.model_validate(create_soil_test(db, current_user, payload))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{farm_id}", response_model=SoilTestRead)
def latest_soil_test(
    farm_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SoilTestRead:
    soil_test = get_latest_soil_test(db, farm_id, current_user)
    if not soil_test:
        raise HTTPException(status_code=404, detail="Soil test not found")
    return SoilTestRead.model_validate(soil_test)
