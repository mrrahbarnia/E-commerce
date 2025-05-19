from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession

from src.providers.v1.types import ProviderId
from src.providers.v1.models import Provider, ProviderStaff
from src.auth.v1.models import UserIdentity


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


def get_providers_query() -> Select[tuple[ProviderId, str, bool, datetime, str]]:
    # SELECT
    #     p.id,
    #     p.name,
    #     p.is_active,
    #     p.created_at,
    #     ui.identity_value
    # FROM providers p
    # JOIN provider_staff ps ON p.id=ps.provider_id
    # JOIN user_identities ui ON ps.user_id=ui.user_id
    return (
        sa.select(
            Provider.id,
            Provider.name,
            Provider.is_active,
            Provider.created_at,
            UserIdentity.identity_value,
        )
        .select_from(Provider)
        .join(ProviderStaff, Provider.id == ProviderStaff.provider_id)
        .join(UserIdentity, ProviderStaff.user_id == UserIdentity.user_id)
    )
