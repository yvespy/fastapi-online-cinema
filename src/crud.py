from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from starlette import status

from . import models
from .models import Film
from .schemas import FilmCreate, FilmUpdate, UserCreate
from passlib.context import CryptContext

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


async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(models.User).where(models.User.email == email))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user_data: UserCreate):
    hashed_password = pwd_context.hash(user_data.password)

    stmt = select(models.UserGroup).where(models.UserGroup.name == models.UserGroupEnum.USER)
    result = await db.execute(stmt)
    user_group = result.scalars().first()

    if not user_group:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Default user group not found."
        )

    try:
        user = models.User(
            email=user_data.email,
            hashed_password=hashed_password,
            group_id=user_group.id,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    except Exception as e:
        await db.rollback()
        print(f"❌ Error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
