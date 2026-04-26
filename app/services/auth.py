from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.schemas.auth import UserCreate, UserUpdate


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def create_user(db: Session, payload: UserCreate) -> User:
    user = User(
        email=payload.email,
        phone=payload.phone,
        full_name=payload.full_name,
        language_preference=payload.language_preference,
        hashed_password=get_password_hash(payload.password),
        role="farmer",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def update_user_profile(db: Session, user: User, payload: UserUpdate) -> User:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

