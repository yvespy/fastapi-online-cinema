from uuid import UUID
from sqlite3 import IntegrityError

from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.database import get_db
from src.models.movies import MovieModel, CertificationModel, GenreModel, DirectorModel, StarModel
from src.queries.movies import apply_movie_search
from src.schemas.movies import MovieListResponseSchema, MovieListItemSchema, MovieDetailSchema, MovieCreateSchema, \
    MovieUpdateSchema

router = APIRouter(prefix="/movies", tags=["movies"])


@router.get(
    "/",
    response_model=MovieListResponseSchema,
    summary="Get paginated list of movies and ability to search by movie title, genre, description, director, or actor.",
)
async def get_movie_list(
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=20),
        search: str | None = Query(None),
        db: AsyncSession = Depends(get_db),
) -> MovieListResponseSchema:
    offset = (page - 1) * page_size

    stmt = select(MovieModel)

    stmt = apply_movie_search(stmt, search)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    if total == 0:
        return MovieListResponseSchema(items=[], total=0, page=page, page_size=page_size)

    order_by = MovieModel.default_order_by()
    if order_by:
        stmt = stmt.order_by(*order_by)

    stmt = stmt.offset(offset).limit(page_size)

    result = await db.execute(stmt)
    movies = result.scalars().all()

    items = [MovieListItemSchema.model_validate(movie) for movie in movies]

    return MovieListResponseSchema(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/",
    response_model=MovieDetailSchema,
    summary="Allows to add a new movie to the database.",
)
async def create_movie(
        movie_data: MovieCreateSchema,
        db: AsyncSession = Depends(get_db),
) -> MovieDetailSchema:
    stmt = select(MovieModel).where(
        MovieModel.name == movie_data.name,
        MovieModel.year == movie_data.year,
        MovieModel.time == movie_data.time,
    )
    result = await db.execute(stmt)
    if result.scalars().first():
        raise HTTPException(
            status_code=409,
            detail=f"Movie '{movie_data.name}' ({movie_data.year}) already exists."
        )

    try:
        cert_stmt = select(CertificationModel).where(CertificationModel.name == movie_data.certifications)
        cert_result = await db.execute(cert_stmt)
        certification = cert_result.scalars().first()
        if not certification:
            certification = CertificationModel(name=movie_data.certifications)
            db.add(certification)
            await db.flush()

        genres = []
        for name in set(movie_data.genres):
            stmt = select(GenreModel).where(GenreModel.name == name)
            result = await db.execute(stmt)
            genre = result.scalars().first()
            if not genre:
                genre = GenreModel(name=name)
                db.add(genre)
                await db.flush()
            genres.append(genre)

        directors = []
        for name in set(movie_data.directors):
            stmt = select(DirectorModel).where(DirectorModel.name == name)
            result = await db.execute(stmt)
            director = result.scalars().first()
            if not director:
                director = DirectorModel(name=name)
                db.add(director)
                await db.flush()
            directors.append(director)

        stars = []
        for name in set(movie_data.stars):
            stmt = select(StarModel).where(StarModel.name == name)
            result = await db.execute(stmt)
            star = result.scalars().first()
            if not star:
                star = StarModel(name=name)
                db.add(star)
                await db.flush()
            stars.append(star)

        movie = MovieModel(
            name=movie_data.name,
            year=movie_data.year,
            time=movie_data.time,
            imdb=movie_data.imdb,
            votes=movie_data.votes,
            meta_score=movie_data.meta_score,
            gross=movie_data.gross,
            description=movie_data.description,
            price=movie_data.price,
            certifications=certification,
            genres=genres,
            directors=directors,
            stars=stars,
        )

        db.add(movie)
        await db.commit()
        await db.refresh(movie, ["certifications", "genres", "directors", "stars"])

        return MovieDetailSchema.model_validate(movie)

    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Invalid input data: {str(e)}")


@router.get(
    "/{movie_uuid}",
    response_model=MovieDetailSchema,
    summary="Allows to retrieve a movie by its UUID with detail view.",
    responses={
        400: {
            "description": "Movie not found.",
            "content": {
                "application/json": {
                    "example": {"detail": "Movie not found."}
                }
            },
        }
    }
)
async def get_movie_detail(movie_uuid: UUID, db: AsyncSession = Depends(get_db)) -> MovieDetailSchema:
    stmt = (
        select(MovieModel)
        .options(
            joinedload(MovieModel.certifications),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.directors),
            joinedload(MovieModel.stars),
        )
        .where(MovieModel.uuid == movie_uuid)
    )

    result = await db.execute(stmt)
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found.")

    return MovieDetailSchema.model_validate(movie)


@router.delete(
    "/{movie_uuid}",
    summary="Allows to delete a movie by its UUID.",
    responses={
        204: {
            "description": "Movie deleted successfully.",
        },
        404: {
            "description": "Movie not found.",
            "content": {
                "application/json": {
                    "example": {"detail": "Movie with the given UUID was not found."}
                }
            },
        },
    },
    status_code=204
)
async def delete_movie(movie_uuid: UUID, db: AsyncSession = Depends(get_db)):
    stmt = select(MovieModel).where(MovieModel.uuid == movie_uuid)
    result = await db.execute(stmt)
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found.")

    await db.delete(movie)
    await db.commit()

    return {"detail": "Movie deleted successfully."}


@router.patch(
    "/{movie_uuid}",
    summary="Allows to update a movie by its UUID.",
    responses={
        200: {
            "description": "Movie updated successfully.",
            "content": {
                "application/json": {
                    "example": {"detail": "Movie updated successfully."}
                }
            },
        },
    },
)
async def update_movie(
        movie_uuid: UUID,
        movie_data: MovieUpdateSchema,
        db: AsyncSession = Depends(get_db),
):
    stmt = select(MovieModel).where(MovieModel.uuid == movie_uuid)
    result = await db.execute(stmt)
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found.")

    for field, value in movie_data.model_dump(exclude_unset=True).items():
        setattr(movie, field, value)

    try:
        await db.commit()
        await db.refresh(movie)
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Invalid input data: {str(e)}")

    return {"detail": "Movie updated successfully."}
