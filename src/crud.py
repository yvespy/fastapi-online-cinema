from datetime import datetime, timedelta

from fastapi import HTTPException, Depends
from pydantic import EmailStr
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from starlette import status

from . import models
from .database import get_db
from .models import Film, User, UserGroup, UserGroupEnum, ActivationToken, RefreshToken
from .notifications.email import send_activation_email
from .schemas import FilmCreate, FilmUpdate, UserRegistrationRequestSchema
from passlib.context import CryptContext

from .security.passwords import verify_password
from .security.token_manager import create_access_token
from .utils import generate_secure_token

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def create_film(db: AsyncSession, film: FilmCreate):
    new_film = Film(**film.model_dump())
    db.add(new_film)
    await db.commit()
    await db.refresh(new_film)
    return new_film


async def get_film(db: AsyncSession, film_id: int):
    result = await db.execute(select(Film).where(Film.id == film_id))
    film = result.scalar_one_or_none()
    return film


async def get_films(db: AsyncSession):
    result = await db.execute(select(Film))
    films = result.scalars().all()
    return films


async def update_film(db: AsyncSession, film_id: int, film: FilmUpdate):
    result = await db.execute(select(Film).where(Film.id == film_id))
    db_film = result.scalar_one_or_none()
    if not db_film:
        return None

    db_film.title = film.title
    db_film.genre = film.genre
    db_film.price = film.price
    await db.commit()
    await db.refresh(db_film)
    return db_film


async def delete_film(db: AsyncSession, film_id: int):
    result = await db.execute(select(Film).where(Film.id == film_id))
    db_film = result.scalar_one_or_none()
    if not db_film:
        return None
    await db.delete(db_film)
    await db.commit()
    return db_film


async def get_user_by_email(db: AsyncSession, email: EmailStr):
    result = await db.execute(select(models.User).where(models.User.email == email))
    return result.scalar_one_or_none()


async def create_user(user_data: UserRegistrationRequestSchema, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.email == user_data.email)
    result = await db.execute(stmt)
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"A user with this email {user_data.email} already exists.")

    stmt = select(UserGroup).where(UserGroup.name == UserGroupEnum.USER)
    result = await db.execute(stmt)
    user_group = result.scalars().first()
    if not user_group:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User group not found.")

    try:
        hashed_password = pwd_context.hash(user_data.password)
        new_user = User(email=str(user_data.email), hashed_password=hashed_password, group_id=user_group.id,
                        is_active=False)
        db.add(new_user)
        await db.flush()

        activation_token = ActivationToken(user_id=new_user.id)
        db.add(activation_token)

        await db.commit()
        await db.refresh(new_user)
        await db.refresh(activation_token)

        activation_link = f"http://127.0.0.1:8000/activate?token={activation_token.token}"
        send_activation_email(recipient_email=new_user.email, activation_link=activation_link)

        return new_user

    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="An error occured while creating user.") from e


async def activate_user(token: str, db: AsyncSession):
    stmt = select(ActivationToken).where(ActivationToken.token == token)
    result = await db.execute(stmt)
    activation_token = result.scalars().first()

    if not activation_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired activation token.")

    if activation_token.expires_at < datetime.utcnow():
        await db.delete(activation_token)
        await db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired activation token.")

    stmt = select(User).where(User.id == activation_token.user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    user.is_active = True

    await db.delete(activation_token)
    await db.commit()

    return user


async def resend_activation_email(user_email: str, db: AsyncSession):
    stmt = select(User).where(User.email == user_email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is already activated.")

    stmt = select(ActivationToken).where(ActivationToken.user_id == user.id)
    result = await db.execute(stmt)
    token_obj = result.scalar_one_or_none()

    now = datetime.utcnow()
    if token_obj and token_obj.expires_at > now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token is still valid. Check your email."
        )

    else:
        if token_obj:
            await db.delete(token_obj)
            await db.commit()

        new_token = ActivationToken(user_id=user.id, token=generate_secure_token())
        db.add(new_token)
        await db.commit()

        activation_link = f"http://127.0.0.1:8000/activate?token={new_token.token}"
        send_activation_email(user_email, activation_link)

        return {"message": "Activation link has been sent."}


async def login_user(db: AsyncSession, email: EmailStr, password: str):
    user = await get_user_by_email(db, email)

    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not activated."
        )

    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=timedelta(minutes=30)
    )

    stmt = select(RefreshToken).filter_by(user_id=user.id)
    result = await db.execute(stmt)
    old_token = result.scalar_one_or_none()
    if old_token:
        await db.delete(old_token)
        await db.commit()

    new_refresh_token = generate_secure_token(32)
    refresh_obj = RefreshToken(user_id=user.id, token=new_refresh_token)
    db.add(refresh_obj)
    await db.commit()

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
    }


async def logout_user(db: AsyncSession, user_id: int):
    stmt = select(RefreshToken).filter_by(user_id=user_id)
    result = await db.execute(stmt)
    token = result.scalar_one_or_none()

    if token:
        await db.delete(token)
        await db.commit()


async def get_refresh_token(db: AsyncSession, token: str):
    result = await db.execute(select(models.RefreshToken).where(models.RefreshToken.token == token).options(
        selectinload(models.RefreshToken.user)))
    return result.scalar_one_or_none()
