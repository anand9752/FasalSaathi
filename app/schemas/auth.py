from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import ORMModel


class UserBase(ORMModel):
    id: int
    email: EmailStr
    phone: str | None = None
    full_name: str
    language_preference: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    phone: str | None = None
    full_name: str
    language_preference: str = "hi"


class UserUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    language_preference: str | None = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

