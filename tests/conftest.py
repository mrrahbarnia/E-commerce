import asyncio
from typing import Generator, Any, AsyncGenerator

# import docker  # type: ignore[import]
import pytest
import pytest_asyncio
import redis.asyncio as redis
from fastapi.testclient import TestClient
from httpx import AsyncClient

# from async_asgi_testclient import TestClient
from testcontainers.postgres import PostgresContainer  # type: ignore[import]
from testcontainers.redis import RedisContainer  # type: ignore[import]
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncEngine,
    async_sessionmaker,
    AsyncSession,
)

from src.main import app
from src.database import Base, session_maker, redis_conn


@pytest.fixture(scope="session")
def postgres_container() -> Generator[PostgresContainer, Any, None]:
    db_container = PostgresContainer("postgres:17.4")
    db_container.start()
    try:
        yield db_container
    finally:
        db_container.stop()


@pytest.fixture(scope="session")
def redis_container():
    redis_container = RedisContainer("redis:7.2-alpine")
    redis_container.start()
    try:
        yield redis_container
    finally:
        redis_container.stop()


@pytest_asyncio.fixture(scope="session")
async def async_engine(
    postgres_container: PostgresContainer,
) -> AsyncGenerator[AsyncEngine, Any]:
    engine = create_async_engine(
        postgres_container.get_connection_url().replace(
            "postgresql+psycopg2", "postgresql+asyncpg"
        ),
    )
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def async_redis_conn(
    redis_container: RedisContainer,
) -> AsyncGenerator[redis.Redis, None]:
    client = redis.Redis.from_url("redis://redis:6378?decode_responses=True")
    try:
        yield client
    finally:
        await client.aclose()


@pytest_asyncio.fixture(scope="session")
async def setup_db(async_engine: AsyncEngine) -> None:
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@pytest_asyncio.fixture(scope="session")
async def session_maker_fixture(
    async_engine: AsyncEngine,
    async_redis_conn: redis.Redis,
    setup_db: None,  # This ensures this fixture is awaited before creating all tables.
) -> None:
    test_session_maker = async_sessionmaker(async_engine, expire_on_commit=False)
    app.dependency_overrides[session_maker] = test_session_maker
    app.dependency_overrides[redis_conn] = lambda: async_redis_conn


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def client(session_maker_fixture: None) -> AsyncGenerator[TestClient, None]:
    # async with AsyncClient(
    #     transport=ASGITransport(app=app, client=("127.0.0.1", 8000)),
    #     base_url="http://testserver",
    # ) as client:
    # yield client
    with TestClient(app) as client:
        yield client
    # async with AsyncClient(app=app, base_url="http://testserver") as ac:
    #     yield ac
    app.dependency_overrides.clear()
