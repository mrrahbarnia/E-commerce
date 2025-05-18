import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
import redis.asyncio as redis
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncEngine,
    async_sessionmaker,
    AsyncSession,
)

from tests.utils import create_user, get_authenticated_client
from src.main import app
from src.database import Base, session_maker, redis_conn
from src.auth.v1.types import UserRole


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


test_postgres_url = "postgresql+asyncpg://test:test@test_db:5432/test"
test_redis_url = "redis://test_redis:6379?decode_responses=True"

test_engine = create_async_engine(test_postgres_url)


async def override_get_session() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(test_engine, expire_on_commit=False)


async def override_redis_conn() -> AsyncGenerator[redis.Redis, None]:
    client = redis.Redis.from_url(url=test_redis_url)
    try:
        yield client
    finally:
        await client.aclose()


app.dependency_overrides[session_maker] = override_get_session
app.dependency_overrides[redis_conn] = override_redis_conn


@pytest_asyncio.fixture(scope="session")
async def redis_client() -> AsyncGenerator[redis.Redis, None]:
    client = redis.Redis.from_url(test_redis_url)
    try:
        yield client
    finally:
        await client.aclose()


@pytest_asyncio.fixture(scope="session")
async def session_maker_fixture() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(test_engine, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session")
async def db_engine() -> AsyncGenerator[AsyncEngine, None]:
    engine = create_async_engine(test_postgres_url)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _db_schema(db_engine: AsyncEngine):
    try:
        async with db_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        yield
    finally:
        async with db_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="session")
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app, client=("127.0.0.1", 8000)),
        base_url="http://test",
    ) as client:
        yield client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="session")
async def user_creator(session_maker_fixture: async_sessionmaker[AsyncSession]):
    async def _create_user(
        identity_value: str,
        username: str,
        full_name: str,
        password: str,
        role: UserRole,
    ):
        async with session_maker_fixture.begin() as session:
            await create_user(
                session,
                identity_value=identity_value,
                username=username,
                full_name=full_name,
                password=password,
                role=role,
            )

    return _create_user


@pytest_asyncio.fixture(scope="session")
async def authenticated_client_as_customer(user_creator):
    identity_value = "customer@gmail.com"
    username = "customer"
    full_name = "customer"
    password = "12345678"
    role = UserRole.CUSTOMER

    await user_creator(identity_value, username, full_name, password, role)
    client = await get_authenticated_client(identity_value, password)
    yield client
    await client.aclose()


@pytest_asyncio.fixture(scope="session")
async def authenticated_client_as_admin(user_creator):
    identity_value = "admin@gmail.com"
    username = "admin"
    full_name = "admin"
    password = "12345678"
    role = UserRole.ADMIN

    await user_creator(identity_value, username, full_name, password, role)
    client = await get_authenticated_client(identity_value, password)
    yield client
    await client.aclose()
