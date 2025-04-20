from typing import AsyncGenerator

import redis.asyncio as redis
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.config import settings
from src.constants import DB_NAMING_CONVENTION

async_engine: AsyncEngine = create_async_engine(str(settings.POSTGRES_URL))


class Base(DeclarativeBase, MappedAsDataclass):
    metadata = MetaData(naming_convention=DB_NAMING_CONVENTION)
    # type_annotation_map = {}


async def session_maker() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(async_engine, expire_on_commit=False)


async def redis_conn() -> AsyncGenerator[redis.Redis, None]:
    client = redis.Redis.from_url(url=str(settings.REDIS_URL))
    try:
        yield client
    finally:
        await client.aclose()
