import pytest


@pytest.fixture
def movie_payload():
    return {
        "name": "Inception",
        "year": 2010,
        "time": 148,
        "imdb": 8.8,
        "votes": 2000000,
        "meta_score": 74,
        "gross": 829.89,
        "description": "A thief who steals corporate secrets...",
        "price": 9.99,
        "certifications": "pg-13",
        "genres": ["Sci-Fi", "Action"],
        "directors": ["Christopher Nolan"],
        "stars": ["Leonardo DiCaprio"]
    }


@pytest.mark.asyncio
async def test_create_movie_success(client, movie_payload):
    response = await client.post("/movies/", json=movie_payload)

    assert response.status_code == 200

    data = response.json()
    assert data["name"] == "Inception"
    assert data["certifications"]["name"] == "PG-13"
    assert len(data["genres"]) == 2
    assert data["directors"][0]["name"] == "Christopher Nolan"


@pytest.mark.asyncio
async def test_create_movie_duplicate(client, movie_payload):
    await client.post("/movies/", json=movie_payload)

    response = await client.post("/movies/", json=movie_payload)

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_movie_list_empty(client):
    response = await client.get("/movies/")

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 0
    assert data["items"] == []


@pytest.mark.asyncio
async def test_get_movie_list_with_data(client, movie_payload):
    await client.post("/movies/", json=movie_payload)

    response = await client.get("/movies/")
    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["name"] == "Inception"


@pytest.mark.asyncio
async def test_pagination(client, movie_payload):
    for i in range(15):
        payload = movie_payload.copy()
        payload["name"] = f"Movie {i}"
        await client.post("/movies/", json=payload)

    response = await client.get("/movies/?page=2&page_size=10")
    data = response.json()

    assert response.status_code == 200
    assert data["page"] == 2
    assert len(data["items"]) == 5


@pytest.mark.asyncio
async def test_filter_by_year(client, movie_payload):
    movie_payload["year"] = 2000
    await client.post("/movies/", json=movie_payload)

    movie_payload2 = movie_payload.copy()
    movie_payload2["name"] = "New Movie"
    movie_payload2["year"] = 2020
    await client.post("/movies/", json=movie_payload2)

    response = await client.get("/movies/?year_from=2010")
    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["year"] == 2020


@pytest.mark.asyncio
async def test_sort_by_price_asc(client, movie_payload):
    payload1 = movie_payload.copy()
    payload1["name"] = "Cheap"
    payload1["price"] = 5

    payload2 = movie_payload.copy()
    payload2["name"] = "Expensive"
    payload2["price"] = 20

    await client.post("/movies/", json=payload1)
    await client.post("/movies/", json=payload2)

    response = await client.get("/movies/?sort_by=price&sort_dir=asc")
    data = response.json()

    assert data["items"][0]["price"] == 5


@pytest.mark.asyncio
async def test_create_movie_invalid_data(client, movie_payload):
    movie_payload["year"] = "invalid"
    response = await client.post("/movies/", json=movie_payload)
    assert response.status_code == 422
    assert "year" in str(response.json()["detail"])


@pytest.mark.asyncio
async def test_get_movie_detail(client, movie_payload):
    create_resp = await client.post("/movies/", json=movie_payload)
    movie_uuid = create_resp.json()["uuid"]

    response = await client.get(f"/movies/{movie_uuid}")

    assert response.status_code == 200
    assert response.json()["uuid"] == movie_uuid


@pytest.mark.asyncio
async def test_get_movie_detail_not_found(client):
    response = await client.get(
        "/movies/00000000-0000-0000-0000-000000000000"
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_movie_success(client, movie_payload):
    create_resp = await client.post("/movies/", json=movie_payload)
    movie_uuid = create_resp.json()["uuid"]

    response = await client.patch(
        f"/movies/{movie_uuid}",
        json={"price": 15.99}
    )

    assert response.status_code == 200
    assert response.json()["detail"] == "Movie updated successfully."


@pytest.mark.asyncio
async def test_update_movie_not_found(client):
    response = await client.patch(
        "/movies/00000000-0000-0000-0000-000000000000",
        json={"price": 10}
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_movie_success(client, movie_payload):
    create_resp = await client.post("/movies/", json=movie_payload)
    movie_uuid = create_resp.json()["uuid"]

    response = await client.delete(f"/movies/{movie_uuid}")

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_movie_not_found(client):
    response = await client.delete(
        "/movies/00000000-0000-0000-0000-000000000000"
    )

    assert response.status_code == 404
