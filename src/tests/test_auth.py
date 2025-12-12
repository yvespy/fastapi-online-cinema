from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import User, ActivationToken
from src.security.passwords import hash_password


@pytest.mark.asyncio
async def test_register_user_success(client: AsyncClient, test_db):
    payload = {
        "email": "testuser@example.com",
        "password": "StrongPass123!"
    }

    response = await client.post("/auth/register/", json=payload)

    assert response.status_code == 201

    async with test_db() as session:
        from sqlalchemy import select
        from src.models import User

        stmt = select(User).where(User.email == payload["email"])
        result = await session.execute(stmt)
        user = result.scalar_one()

        assert user.is_active is False


@pytest.mark.asyncio
async def test_register_user_conflict(client: AsyncClient):
    payload = {
        "email": "duplicate@example.com",
        "password": "StrongPass123!"
    }

    first = await client.post("/auth/register/", json=payload)
    assert first.status_code == 201

    second = await client.post("/auth/register/", json=payload)

    assert second.status_code == 409
    assert "already exists" in second.json()["detail"]


@pytest.mark.asyncio
async def test_activate_user_success(async_client: AsyncClient, async_session: AsyncSession):
    user = User(
        email="test_activate@example.com",
        hashed_password=hash_password("password123"),
        is_active=False,
        group="USER",
    )
    async_session.add(user)
    await async_session.flush()  # get user.id

    token = ActivationToken(
        user_id=user.id,
        token="valid-test-token",
        expires_at=datetime.utcnow() + timedelta(hours=1),
    )
    async_session.add(token)
    await async_session.commit()

    response = await async_client.post("/auth/activate/?token=valid-test-token")

    assert response.status_code == 200
    assert response.json()["message"] == "User successfully activated."

    refreshed_user = await async_session.get(User, user.id)
    assert refreshed_user.is_active is True

    deleted_token = await async_session.get(ActivationToken, token.id)
    assert deleted_token is None


@pytest.mark.asyncio
async def test_activate_user_invalid_token(async_client: AsyncClient):
    response = await async_client.post("/auth/activate/?token=wrong-token")
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid or expired activation token."
