import logging
from datetime import datetime

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.admin.v1 import repositories
from src.admin.v1 import exceptions
from src.common.exceptions import CheckDbConnection
from src.common.pagination import (
    PaginationQueryParamsSchema,
    PaginatedResponse,
    apply_pagination,
)
from src.providers.v1.types import ProviderId

from src.admin.v1.schemas import ProvidersOut


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


async def get_providers(
    request: Request,
    session_maker: async_sessionmaker[AsyncSession],
    pagination_query: PaginationQueryParamsSchema,
) -> PaginatedResponse[ProvidersOut]:
    query = repositories.get_providers_query()

    def mapper_function(
        row: tuple[ProviderId, str, bool, datetime, str],
    ) -> ProvidersOut:
        return ProvidersOut(
            provider_id=row[0],
            name=row[1],
            is_active=row[2],
            created_at=row[3],
            founder_identity_value=row[4],
        )

    try:
        async with session_maker.begin() as session:
            return await apply_pagination(
                request, session, query, pagination_query, mapper_function
            )
    except Exception as ex:
        logger.warning(ex)
        raise CheckDbConnection
