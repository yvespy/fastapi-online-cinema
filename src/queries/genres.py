from sqlalchemy import Select, select, func

from src.models.movies import GenreModel, movie_genres


def get_genres_with_movie_count() -> Select:
    return (
        select(
            GenreModel.id,
            GenreModel.name,
            func.count(movie_genres.c.movie_id).label("movie_count"),
        )
        .outerjoin(movie_genres, GenreModel.id == movie_genres.c.genre_id)
        .group_by(GenreModel.id)
    )
