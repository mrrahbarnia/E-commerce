from typing import AsyncGenerator
from datetime import datetime

import redis.asyncio as redis
from sqlalchemy import MetaData, types as sql_types
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.config import settings
from src.constants import DB_NAMING_CONVENTION
from src.auth.v1 import types as auth_types
from src.providers.v1 import types as sellers_types

async_engine: AsyncEngine = create_async_engine(str(settings.POSTGRES_URL))


class Base(DeclarativeBase, MappedAsDataclass):
    metadata = MetaData(naming_convention=DB_NAMING_CONVENTION)
    type_annotation_map = {
        datetime: sql_types.TIMESTAMP(timezone=True),
        auth_types.UserId: sql_types.UUID,
        auth_types.UserIdentityId: sql_types.INTEGER,
        auth_types.RoleId: sql_types.INTEGER,
        auth_types.PermissionId: sql_types.INTEGER,
        sellers_types.ProviderId: sql_types.UUID,
        sellers_types.ProviderStaffId: sql_types.INTEGER,
    }


async def session_maker() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(async_engine, expire_on_commit=False)


async def redis_conn() -> AsyncGenerator[redis.Redis, None]:
    client = redis.Redis.from_url(url=str(settings.REDIS_URL))
    try:
        yield client
    finally:
        await client.aclose()
