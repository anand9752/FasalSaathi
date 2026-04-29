from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.kisan_news import KisanNewsResponse
from app.services.kisan_news import get_kisan_news


router = APIRouter()


@router.get("", response_model=KisanNewsResponse)
def kisan_news(
    limit: int = Query(default=8, ge=5, le=10),
    force_refresh: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> KisanNewsResponse:
    return get_kisan_news(db, limit=limit, force_refresh=force_refresh)

