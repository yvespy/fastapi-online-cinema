import uuid
from sqlalchemy import Table, Column, ForeignKey, Integer, String, UUID, Float, Text, DECIMAL, UniqueConstraint
from sqlalchemy.orm import relationship

from src.models.base import Base

movie_genres = Table(
    "movie_genres",
    Base.metadata,
    Column(
        "movie_id",
        ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True, nullable=False),
    Column(
        "genre_id",
        ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True, nullable=False),
)

movie_directors = Table(
    "movie_directors",
    Base.metadata,
    Column(
        "movie_id",
        ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True, nullable=False),
    Column(
        "director_id",
        ForeignKey("directors.id", ondelete="CASCADE"), primary_key=True, nullable=False)
)

movie_stars = Table(
    "movie_stars",
    Base.metadata,
    Column(
        "movie_id",
        ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True, nullable=False),
    Column(
        "star_id",
        ForeignKey("stars.id", ondelete="CASCADE"), primary_key=True, nullable=False)
)


class GenreModel(Base):
    __tablename__ = "genres"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)

    movies = relationship("MovieModel", secondary=movie_genres, back_populates="genres")

    def __repr__(self) -> str:
        return f"<Genre(id={self.id}, name='{self.name}'>)"


class StarModel(Base):
    __tablename__ = "stars"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)

    movies = relationship("MovieModel", secondary=movie_stars, back_populates="stars")

    def __repr__(self) -> str:
        return f"<Star(id={self.id}, name='{self.name}'>)"


class DirectorModel(Base):
    __tablename__ = "directors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)

    movies = relationship("MovieModel", secondary=movie_directors, back_populates="directors")

    def __repr__(self) -> str:
        return f"<Director(id={self.id}, name='{self.name}'>)"


class CertificationModel(Base):
    __tablename__ = "certifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)

    movies = relationship("MovieModel", back_populates="certifications")

    def __repr__(self) -> str:
        return f"<Certification(id={self.id}, name='{self.name}'>)"


class MovieModel(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)

    name = Column(String(255), nullable=False)
    year = Column(Integer, nullable=False)
    time = Column(Integer, nullable=False)

    imdb = Column(Float, nullable=False)
    votes = Column(Integer, nullable=False)

    meta_score = Column(Float, nullable=True)
    gross = Column(Float, nullable=True)

    description = Column(Text, nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False, default=0)

    certifications_id = Column(Integer, ForeignKey("certifications.id", ondelete="RESTRICT"), nullable=False)
    certifications = relationship(
        "CertificationModel",
        back_populates="movies"
    )
    genres = relationship(
        "GenreModel",
        secondary=movie_genres,
        back_populates="movies",
    )
    directors = relationship(
        "DirectorModel",
        secondary=movie_directors,
        back_populates="movies",
    )
    stars = relationship(
        "StarModel",
        secondary=movie_stars,
        back_populates="movies",
    )

    __table_args__ = (
        UniqueConstraint(
            "name",
            "year",
            "time",
            name="uq_movie_identity",
        ),
    )

    def __repr__(self) -> str:
        return f"<Movie(id={self.id}, name='{self.name}', year={self.year}>)"
