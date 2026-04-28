from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.calendar import FarmCalendarResponse
from app.services.farm_calendar import build_farm_calendar


router = APIRouter()


@router.get("/farm-calendar", response_model=FarmCalendarResponse)
def get_farm_calendar(
    farm_id: int | None = Query(default=None, ge=1),
    lat: float | None = Query(default=None),
    lon: float | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> FarmCalendarResponse:
    return build_farm_calendar(db, current_user.id, farm_id=farm_id, lat=lat, lon=lon)
