from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from src.models.accounts import User, ActivationToken, RefreshToken
from src.security.passwords import hash_password, verify_password
from src.security.token_manager import create_access_token


@pytest.mark.asyncio
async def test_user_registration_success(client, db_session, seed_user_groups):
    payload = {"email": "test@example.com", "password": "StrongPassword123!"}

    response = await client.post("/auth/register/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == payload["email"]

    result = await db_session.execute(select(User).where(User.email == payload["email"]))
    user = result.scalars().first()
    assert user is not None
    assert not user.is_active

    result = await db_session.execute(select(ActivationToken).where(ActivationToken.user_id == user.id))
    token = result.scalars().first()
    assert token is not None
    assert token.token is not None


@pytest.mark.asyncio
async def test_activate_user_success(client, db_session, seed_user_groups):
    user = User(
        email="inactive@example.com",
        hashed_password=hash_password("StrongPassword123!"),
        is_active=False,
        group_id=1,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    activation_token = ActivationToken(
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    db_session.add(activation_token)
    await db_session.commit()
    await db_session.refresh(activation_token)

    token_id = activation_token.id

    response = await client.post(
        f"/auth/activate/?token={activation_token.token}"
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "User successfully activated."
    }

    await db_session.refresh(user)
    assert user.is_active is True

    db_session.expire_all()

    result = await db_session.execute(
        select(ActivationToken).where(ActivationToken.id == token_id)
    )
    token_in_db = result.scalar_one_or_none()

    assert token_in_db is None


@pytest.mark.asyncio
async def test_activate_user_invalid_token(client):
    response = await client.post("/auth/activate/?token=invalidtoken")
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid or expired activation token."


@pytest.mark.asyncio
async def test_activate_user_expired_token(
        client,
        db_session,
        seed_user_groups,
):
    user = User(
        email="expired@example.com",
        hashed_password=hash_password("StrongPassword123!"),
        is_active=False,
        group_id=1,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    activation_token = ActivationToken(
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),  # 👈 expired
    )
    db_session.add(activation_token)
    await db_session.commit()
    await db_session.refresh(activation_token)

    token_id = activation_token.id

    response = await client.post(
        f"/auth/activate/?token={activation_token.token}"
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid or expired activation token."

    await db_session.refresh(user)
    assert user.is_active is False

    db_session.expire_all()

    result = await db_session.execute(
        select(ActivationToken).where(ActivationToken.id == token_id)
    )
    token_in_db = result.scalar_one_or_none()

    assert token_in_db is None


@pytest.mark.asyncio
async def test_activate_user_token_already_used(
        client,
        db_session,
        seed_user_groups,
):
    user = User(
        email="used@example.com",
        hashed_password=hash_password("StrongPassword123!"),
        is_active=False,
        group_id=1,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    activation_token = ActivationToken(
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    db_session.add(activation_token)
    await db_session.commit()
    await db_session.refresh(activation_token)

    token_value = activation_token.token

    response_first = await client.post(
        f"/auth/activate/?token={token_value}"
    )

    assert response_first.status_code == 200

    response_second = await client.post(
        f"/auth/activate/?token={token_value}"
    )

    assert response_second.status_code == 400
    assert response_second.json()["detail"] == "Invalid or expired activation token."

    await db_session.refresh(user)
    assert user.is_active is True


@pytest.mark.asyncio
async def test_login_success(
        client,
        db_session,
        seed_user_groups,
):
    user = User(
        email="login@example.com",
        hashed_password=hash_password("StrongPassword123!"),
        is_active=True,
        group_id=1,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    response = await client.post(
        "/auth/login/",
        json={
            "email": "login@example.com",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert isinstance(data["access_token"], str)
    assert isinstance(data["refresh_token"], str)

    result = await db_session.execute(
        select(RefreshToken).where(RefreshToken.user_id == user.id)
    )
    refresh = result.scalar_one_or_none()

    assert refresh is not None
    assert refresh.token == data["refresh_token"]


@pytest.mark.asyncio
async def test_login_invalid_email(client):
    response = await client.post(
        "/auth/login/",
        json={
            "email": "wrong@example.com",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password."


@pytest.mark.asyncio
async def test_login_invalid_password(
        client,
        db_session,
        seed_user_groups,
):
    user = User(
        email="wrongpass@example.com",
        hashed_password=hash_password("CorrectPassword123!"),
        is_active=True,
        group_id=1,
    )
    db_session.add(user)
    await db_session.commit()

    response = await client.post(
        "/auth/login/",
        json={
            "email": "wrongpass@example.com",
            "password": "AnotherValidPassword123!",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password."


@pytest.mark.asyncio
async def test_login_user_not_activated(
        client,
        db_session,
        seed_user_groups,
):
    user = User(
        email="login_inactive@example.com",
        hashed_password=hash_password("StrongPassword123!"),
        is_active=False,
        group_id=1,
    )
    db_session.add(user)
    await db_session.commit()

    response = await client.post(
        "/auth/login/",
        json={
            "email": "login_inactive@example.com",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "User account is not activated."


@pytest.mark.asyncio
async def test_refresh_token_success(
        client,
        db_session,
        seed_user_groups,
):
    user = User(
        email="refresh_success@example.com",
        hashed_password=hash_password("StrongPassword123!"),
        is_active=True,
        group_id=1,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    refresh_token = RefreshToken(
        user_id=user.id,
        token="valid_refresh_token_123",
    )
    db_session.add(refresh_token)
    await db_session.commit()

    response = await client.post(
        "/auth/refresh/",
        json={"refresh_token": "valid_refresh_token_123"},
    )

    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert isinstance(data["access_token"], str)
    assert len(data["access_token"]) > 10


@pytest.mark.asyncio
async def test_refresh_token_not_found(
        client,
        db_session,
):
    response = await client.post(
        "/auth/refresh/",
        json={"refresh_token": "non_existing_token"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Refresh token not found."


@pytest.mark.asyncio
async def test_logout_success(
        client,
        db_session,
        seed_user_groups,
):
    user = User(
        email="logout@example.com",
        hashed_password=hash_password("Password123!"),
        is_active=True,
        group_id=1,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    refresh = RefreshToken(
        user_id=user.id,
        token="valid_refresh_token",
    )
    db_session.add(refresh)
    await db_session.commit()

    response = await client.post(
        "/auth/logout/",
        params={"token": "valid_refresh_token"},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Logged out successfully."}

    result = await db_session.execute(
        select(RefreshToken).where(RefreshToken.token == "valid_refresh_token")
    )
    assert result.scalars().first() is None


@pytest.mark.asyncio
async def test_logout_invalid_token(
        client,
        db_session,
        seed_user_groups,
):
    response = await client.post(
        "/auth/logout/",
        params={"token": "non_existing_token"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid token."}


@pytest.mark.asyncio
async def test_change_password_success(client, db_session, test_user):
    old_password = "OldPassword123!"
    new_password = "NewStrongPassword123!"

    test_user.hashed_password = hash_password(old_password)
    db_session.add(test_user)
    await db_session.commit()
    await db_session.refresh(test_user)

    access_token = create_access_token({"sub": str(test_user.id)})

    response = await client.post(
        "/auth/change-password/",
        json={
            "old_password": old_password,
            "new_password": new_password,
        },
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Password changed successfully."

    stmt = select(User).where(User.id == test_user.id)
    result = await db_session.execute(stmt)
    updated_user = result.scalars().first()
    await db_session.refresh(updated_user)

    assert verify_password(new_password, updated_user.hashed_password)
