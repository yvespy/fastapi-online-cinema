import asyncio

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy import select

from src.main import app
from src.models.accounts import Base, UserGroupEnum, UserGroup, User
from src.database import get_db
from src.config.dependencies import get_email_sender
from src.security.passwords import hash_password
from src.tests.stubs.email_stub import StubEmailSender


def pytest_configure(config):
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine_test = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
)

AsyncSessionTest = async_sessionmaker(
    bind=engine_test,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def prepare_database():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def db_session():
    async with AsyncSessionTest() as session:
        yield session


async def override_get_db():
    async with AsyncSessionTest() as session:
        yield session


@pytest.fixture(autouse=True)
def override_db():
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()

@pytest_asyncio.fixture(scope="function")
async def email_sender_stub():
    return StubEmailSender()


@pytest.fixture(autouse=True)
def override_email_sender(email_sender_stub):
    app.dependency_overrides[get_email_sender] = lambda: email_sender_stub
    yield
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client():
    app.dependency_overrides[get_email_sender] = lambda: StubEmailSender()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session, seed_user_groups):
    user = User(
        email="testuser@example.com",
        hashed_password=hash_password("InitialPassword123!"),
        is_active=True,
        group_id=1,  # або 1, якщо enum == id
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def seed_user_groups(db_session: AsyncSession):
    for group in UserGroupEnum:
        exists = await db_session.scalar(
            select(UserGroup).where(UserGroup.name == group.value)
        )
        if not exists:
            db_session.add(UserGroup(name=group.value))

    await db_session.commit()
    yield
