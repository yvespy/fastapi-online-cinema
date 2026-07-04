from sqlalchemy import or_
from sqlalchemy.sql import Select

from src.models.movies import MovieModel, GenreModel, DirectorModel, StarModel

SORT_FIELDS = {
    "price": MovieModel.price,
    "year": MovieModel.year,
    "imdb": MovieModel.imdb,
    "popularity": MovieModel.votes,
}


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


def apply_movie_filters(
        stmt: Select,
        *,
        year_from: int | None = None,
        year_to: int | None = None,
        imdb_from: int | None = None,
        imdb_to: int | None = None,
        genre_id: int | None = None,
) -> Select:
    """Filter movies by year and imdb rating"""
    if year_from is not None:
        stmt = stmt.where(MovieModel.year >= year_from)

    if year_to is not None:
        stmt = stmt.where(MovieModel.year <= year_to)

    if imdb_from is not None:
        stmt = stmt.where(MovieModel.imdb >= imdb_from)

    if imdb_to is not None:
        stmt = stmt.where(MovieModel.imdb <= imdb_to)

    if genre_id:
        stmt = stmt.where(
            MovieModel.genres.any(GenreModel.id == genre_id)
        )

    return stmt


def apply_movie_sorting(
        stmt: Select,
        sort_by: str | None = None,
        sort_dir: str | None = None,
) -> Select:
    """Sorting movies by year, imdb rating, price and popularity."""
    if not sort_by or sort_by not in SORT_FIELDS:
        return stmt

    column = SORT_FIELDS[sort_by]
    return stmt.order_by(column.desc() if sort_dir == "desc" else column.asc())
