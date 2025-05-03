import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from src.providers.v1.types import ProviderId
from src.providers.v1.models import Provider


async def get_provider_is_active(
    db_session: AsyncSession, provider_id: ProviderId
) -> bool | None:
    smtm = sa.select(Provider.is_active).where(Provider.id == provider_id)
    return await db_session.scalar(smtm)


async def update_provider_is_active(
    db_session: AsyncSession, provider_id: ProviderId
) -> None:
    smtm = sa.update(Provider).where(Provider.id == provider_id).values(is_active=True)
    await db_session.execute(smtm)
