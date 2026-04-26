from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.dashboard import DashboardOverview
from app.services.dashboard import build_dashboard_overview


router = APIRouter()


@router.get("/overview", response_model=DashboardOverview)
def dashboard_overview(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)
) -> DashboardOverview:
    return build_dashboard_overview(db, current_user.id)
