from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.core.config import settings
from app.core.security import create_access_token
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import Token, UserBase, UserCreate
from app.services.auth import authenticate_user, create_user, get_user_by_email


router = APIRouter()


@router.post("/register", response_model=UserBase, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    existing = get_user_by_email(db, payload.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    return create_user(db, payload)


@router.post("/token", response_model=Token)
def login_access_token(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Token:
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    return Token(access_token=create_access_token(user.id, expires_delta=access_token_expires))


@router.get("/me", response_model=UserBase)
def read_current_user(current_user: User = Depends(get_current_active_user)) -> User:
    return current_user
