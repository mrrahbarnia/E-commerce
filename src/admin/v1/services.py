import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.admin.v1 import repositories
from src.admin.v1 import exceptions
from src.common.exceptions import CheckDbConnection
from src.providers.v1.types import ProviderId


logger = logging.getLogger("admin")


async def verify_provider(
    session_maker: async_sessionmaker[AsyncSession],
    provider_id: ProviderId,
) -> None:
    try:
        async with session_maker.begin() as session:
            is_active = await repositories.get_provider_is_active(
                db_session=session, provider_id=provider_id
            )
            if is_active is None:
                raise exceptions.ProviderNotFoundExc
            if is_active is True:
                raise exceptions.ProviderAlreadyIsActiveExc
            await repositories.update_provider_is_active(
                db_session=session, provider_id=provider_id
            )
    except exceptions.ProviderNotFoundExc as ex:
        logger.warning(ex)
        raise ex
    except exceptions.ProviderAlreadyIsActiveExc as ex:
        logger.warning(ex)
        raise ex
    except Exception as ex:
        logger.error(ex)
        raise CheckDbConnection
