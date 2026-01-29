import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel, Field, field_validator

from src.schemas.examples.movies import genre_schema_example, star_schema_example, director_schema_example, \
    certification_schema_example, movie_list_item_schema_example, movie_list_response_schema_example, \
    movie_detail_schema_example, movie_create_schema_example, movie_update_schema_example


class GenreSchema(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": genre_schema_example
        }
    }


class StarSchema(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": star_schema_example
        }
    }


class DirectorSchema(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": director_schema_example
        }
    }


class CertificationSchema(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": certification_schema_example
        }
    }


class MovieBaseSchema(BaseModel):
    name: str = Field(..., max_length=255)
    year: int = Field(..., ge=1888)
    time: int = Field(..., gt=0)

    imdb: float = Field(..., ge=0, le=10)
    votes: int = Field(..., ge=0)

    meta_score: Optional[float] = Field(None, ge=0, le=100)
    gross: Optional[float] = Field(None, ge=0)

    description: str
    price: float = Field(..., ge=0)

    model_config = {
        "from_attributes": True
    }

    @field_validator("year")
    @classmethod
    def validate_year(cls, v: int) -> int:
        current_year = datetime.now().year
        if v > current_year + 1:
            raise ValueError(f"The year cannot be greater than {current_year + 1}.")
        return v


class MovieListItemSchema(BaseModel):
    id: int
    uuid: uuid.UUID
    name: str
    year: int
    imdb: float
    price: float

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": movie_list_item_schema_example
        }
    }


class MovieListResponseSchema(BaseModel):
    items: List[MovieListItemSchema]
    total: int
    page: int
    page_size: int

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": movie_list_response_schema_example
        }
    }


class MovieDetailSchema(MovieBaseSchema):
    id: int
    uuid: uuid.UUID

    certifications: CertificationSchema
    genres: List[GenreSchema]
    directors: List[DirectorSchema]
    stars: List[StarSchema]

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": movie_detail_schema_example
        }
    }


class MovieCreateSchema(BaseModel):
    name: str = Field(..., max_length=255)

    year: int = Field(..., ge=1888)
    time: int = Field(..., ge=0)

    imdb: float = Field(..., ge=0, le=10)
    votes: int = Field(..., ge=0)

    meta_score: Optional[float] = Field(None, ge=0, le=100)
    gross: Optional[float] = Field(None, ge=0)

    description: str
    price: float = Field(..., ge=0)

    certifications: str

    genres: List[str]
    directors: List[str]
    stars: List[str]
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": movie_create_schema_example
        }
    }

    @field_validator("certifications", mode="before")
    @classmethod
    def normalize_certification(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("genres", "directors", "stars", mode="before")
    @classmethod
    def normalize_list_fields(cls, v: List[str]) -> List[str]:
        return [item.strip().title() for item in v]


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=255)

    year: Optional[int] = Field(None, ge=1888)
    time: Optional[int] = Field(None, gt=0)

    imdb: Optional[float] = Field(None, ge=0, le=10)
    votes: Optional[int] = Field(None, ge=0)

    meta_score: Optional[float] = Field(None, ge=0, le=100)
    gross: Optional[float] = Field(None, ge=0)

    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, ge=0)

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": movie_update_schema_example
        }
    }
