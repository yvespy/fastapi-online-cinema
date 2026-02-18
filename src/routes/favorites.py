from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.database import get_db
from src.models.movies import MovieModel, user_favorites
from src.models.accounts import User
from src.routes.auth import get_current_user
from src.schemas.movies import MovieListItemSchema

router = APIRouter(prefix="/favorites", tags=["Favorites"])


@router.get("/", response_model=list[MovieListItemSchema], summary="Get list of favorites movies for current user.")
async def get_favorites(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    stmt = (
        select(MovieModel)
        .join(user_favorites)
        .where(user_favorites.c.user_id == current_user.id)
    )

    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/{movie_id}", status_code=204, summary="Add movie to favorite by id.")
async def add_to_favorites(
        movie_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    stmt = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    stmt = (
        select(user_favorites)
        .where(
            user_favorites.c.user_id == current_user.id,
            user_favorites.c.movie_id == movie_id,
        )
    )
    result = await db.execute(stmt)

    if result.first():
        return

    await db.execute(
        user_favorites.insert().values(
            user_id=current_user.id,
            movie_id=movie_id,
        )
    )

    await db.commit()


@router.delete("/{movie_id}", status_code=204, summary="Allows to delete a movie for favorites by its id.",
               responses={
                   204: {
                       "description": "Movie deleted from favorites.",
                   },
                   400: {
                       "description": "Movie not in favorites.",
                   }
               })
async def remove_from_favorites(
        movie_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    stmt = (
        select(user_favorites)
        .where(
            user_favorites.c.user_id == current_user.id,
            user_favorites.c.movie_id == movie_id,
        )
    )
    result = await db.execute(stmt)

    if not result.first():
        raise HTTPException(status_code=400, detail="Movie not in favorites")

    await db.execute(
        user_favorites.delete().where(
            user_favorites.c.user_id == current_user.id,
            user_favorites.c.movie_id == movie_id,
        )
    )

    await db.commit()
