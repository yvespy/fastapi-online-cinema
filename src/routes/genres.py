from fastapi import APIRouter
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.queries.genres import get_genres_with_movie_count
from src.schemas.movies import GenreWithCountSchema

router = APIRouter(prefix="/genres", tags=["Genres"])


@router.get("/", response_model=list[GenreWithCountSchema], summary="Get list of genres with movies count")
async def get_genres(db: AsyncSession = Depends(get_db)):
    stmt = get_genres_with_movie_count()
    result = await db.execute(stmt)
    return result.all()
