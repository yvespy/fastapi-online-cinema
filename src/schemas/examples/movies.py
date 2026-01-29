genre_schema_example = {
    "id": 1,
    "name": "Action",
}

star_schema_example = {
    "id": 1,
    "name": "Leonardo DiCaprio",
}

director_schema_example = {
    "id": 1,
    "name": "Christopher Nolan",
}

certification_schema_example = {
    "id": 1,
    "name": "PG-13",
}

movie_list_item_schema_example = {
    "id": 1,
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Inception",
    "year": 2010,
    "imdb": 8.8,
    "price": 9.99,
}

movie_list_response_schema_example = {
    "items": [movie_list_item_schema_example],
    "total": 1,
    "page": 1,
    "page_size": 10,
}

movie_detail_schema_example = {
    "id": 1,
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Inception",
    "year": 2010,
    "time": 148,
    "imdb": 8.8,
    "votes": 2200000,
    "meta_score": 74,
    "gross": 829895144,
    "description": (
        "A skilled thief who steals corporate secrets through the use of dream-sharing "
        "technology is given the inverse task of planting an idea into the mind of a CEO."
    ),
    "price": 9.99,
    "certifications": certification_schema_example,
    "genres": [
        genre_schema_example
    ],
    "directors": [
        director_schema_example
    ],
    "stars": [
        star_schema_example
    ],
}

movie_create_schema_example = {
    "name": "Inception",
    "year": 2010,
    "time": 148,
    "imdb": 8.8,
    "votes": 2200000,
    "meta_score": 74,
    "gross": 829895144,
    "description": (
        "A skilled thief who steals corporate secrets through the use of dream-sharing "
        "technology is given the inverse task of planting an idea into the mind of a CEO."
    ),
    "price": 9.99,
    "certifications": "PG-13",
    "genres": ["Action", "Sci-Fi"],
    "directors": ["Christopher Nolan"],
    "stars": ["Leonardo DiCaprio"],
}

movie_update_schema_example = {
    "name": "Inception",
    "year": 2010,
    "time": 148,
    "imdb": 8.8,
    "votes": 2200000,
    "meta_score": 74,
    "gross": 829895144,
    "description": (
        "A skilled thief who steals corporate secrets through the use of dream-sharing "
        "technology is given the inverse task of planting an idea into the mind of a CEO."
    ),
    "price": 9.99,
}
