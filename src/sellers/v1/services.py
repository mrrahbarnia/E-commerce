import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.sellers.v1 import exceptions
from src.sellers.v1 import repositories
from src.sellers.v1 import types
from src.common.exceptions import CheckDbConnection
from src.auth.v1.types import UserId
from src.auth.v1 import repositories as auth_repositories

logger = logging.getLogger("sellers")


async def add_staff(
    session_maker: async_sessionmaker[AsyncSession],
    seller_id: types.SellerId,
    user_id: UserId,
):
    try:
        async with session_maker.begin() as session:
            is_staff_active = await auth_repositories.check_user_is_active(
                session, user_id
            )
            if is_staff_active is None:
                raise exceptions.StaffNotFoundExc
            await repositories.create_seller_staff(session, seller_id, user_id)
    except exceptions.StaffNotFoundExc as ex:
        logger.info(ex)
        raise ex
    except Exception as ex:
        logger.error(ex)
        raise CheckDbConnection
