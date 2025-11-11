from datetime import datetime, timezone, timedelta
from enum import Enum

from sqlalchemy import Column, Integer, String, Float, Enum as SqlEnum, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from src.utils import generate_secure_token

Base = declarative_base()


class UserGroupEnum(str, Enum):
    USER = "USER"
    MODERATOR = "MODERATOR"
    ADMIN = "ADMIN"


class GenderEnum(str, Enum):
    MAN = "man"
    WOMAN = "woman"


class UserGroup(Base):
    __tablename__ = "user_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(SqlEnum(UserGroupEnum), unique=True, nullable=False)

    users = relationship("User", back_populates="group")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    group_id = Column(Integer, ForeignKey("user_groups.id"), nullable=False)
    group = relationship("UserGroup", back_populates="users")
    activation_token = relationship("ActivationToken", back_populates="users", uselist=False)
    password_reset_token = relationship("PasswordResetToken", back_populates="users", uselist=False)
    refresh_token = relationship("RefreshToken", back_populates="users", cascade="all, delete-orphan")
    profile = relationship("UserProfile", back_populates="users", uselist=False)


class UserProfileModel(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    avatar = Column(String(255), nullable=False)
    gender = Column(SqlEnum(UserGroupEnum), nullable=False)
    date_of_birth = Column(DateTime, nullable=False)
    info = Column(Text, nullable=False)

    user = relationship("User", back_populates="profile")


class TokenBaseModel(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(64), unique=True, nullable=False, default=generate_secure_token)
    expires_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc) + timedelta(days=1))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)


class ActivationToken(TokenBaseModel):
    __tablename__ = "activation_tokens"

    user = relationship("User", back_populates="activation_token")


class PasswordResetToken(TokenBaseModel):
    __tablename__ = "password_reset_tokens"

    user = relationship("User", back_populates="password_reset_token")


class RefreshToken(TokenBaseModel):
    __tablename__ = "refresh_tokens"

    user = relationship("User", back_populates="refresh_token")
    token = Column(String(512), unique=True, nullable=False, default=generate_secure_token)

    @classmethod
    def create(cls, user_id: int, days_valid: int = 30) -> "RefreshToken":
        """
        Factory method to create a RefreshToken instance
        """
        expires_at = datetime.now(timezone.utc) + timedelta(days=days_valid)
        return cls(user_id=user_id, expires_at=expires_at)


class Film(Base):
    __tablename__ = "films"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    genre = Column(String, index=True, nullable=False)
    price = Column(Float, nullable=False)
