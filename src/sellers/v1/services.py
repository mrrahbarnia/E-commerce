import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.auth.v1.types import UserId

logger = logging.getLogger("sellers")


async def add_member(session_maker: async_sessionmaker[AsyncSession], user_id: UserId):
    async with session_maker.begin() as session:
        ...
