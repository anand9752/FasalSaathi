from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import UserBase, UserUpdate
from app.services.auth import update_user_profile


router = APIRouter()


@router.get("/me", response_model=UserBase)
def get_profile(current_user: User = Depends(get_current_active_user)) -> User:
    return current_user


@router.put("/me", response_model=UserBase)
def update_profile(
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> User:
    return update_user_profile(db, current_user, payload)
