from sqlalchemy import or_
from sqlalchemy.sql import Select

from src.models.movies import MovieModel, GenreModel, DirectorModel, StarModel


def apply_movie_search(stmt: Select, search: str) -> Select:
    """Query for searching movies, genres, description, directors, and stars"""
    if not search:
        return stmt

    search = f"%{search}%"

    return stmt.where(
        or_(
            MovieModel.name.ilike(search),
            MovieModel.description.ilike(search),
            MovieModel.genres.any(GenreModel.name.ilike(search)),
            MovieModel.directors.any(DirectorModel.name.ilike(search)),
            MovieModel.stars.any(StarModel.name.ilike(search)),
        )
    )
