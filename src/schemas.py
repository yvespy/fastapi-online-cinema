from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr

from src.models import UserGroup


class FilmBase(BaseModel):
    title: str
    genre: str
    price: float


class FilmCreate(FilmBase):
    pass


class FilmUpdate(FilmBase):
    pass


class FilmRead(FilmBase):
    id: int

    class Config:
        from_attributes = True


class UserGroupEnum(str, Enum):
    USER = "USER"
    MODERATOR = "MODERATOR"
    ADMIN = "ADMIN"


class UserGroupRead(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    is_active: bool
    group_id: int
    created_at: datetime

    class Config:
        from_attributes = True
