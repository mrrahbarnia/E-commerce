import logging

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from src.providers.v1 import models
from src.providers.v1 import types
from src.auth.v1.types import UserId, UserRole
from src.auth.v1.models import User

logger = logging.getLogger("sellers")


async def create_provider_staff(
    db_session: AsyncSession,
    provider_id: types.ProviderId,
    user_id: UserId,
    is_founder: bool = False,
) -> None:
    smtm = sa.insert(models.ProviderStaff).values(
        {
            models.ProviderStaff.is_founder: is_founder,
            models.ProviderStaff.provider_id: provider_id,
            models.ProviderStaff.user_id: user_id,
        }
    )
    await db_session.execute(smtm)


async def create_provider(
    db_session: AsyncSession, name: str
) -> types.ProviderId | None:
    smtm = (
        sa.insert(models.Provider)
        .values({models.Provider.name: name})
        .returning(models.Provider.id)
    )
    return await db_session.scalar(smtm)


async def check_staff_status_before_invitation(
    db_session: AsyncSession, user_id: UserId
) -> tuple[bool, UserRole, types.InvitationStatus] | None:
    # SELECT u.is_active, u.role, si.status
    # FROM users u
    # LEFT JOIN staff_invitations si
    # ON u.id=si.user_id
    # WHERE u.id='06a0b637-7475-4ed8-86de-d252162cf650'::UUID
    smtm = (
        sa.select(User.is_active, User.role, models.StaffInvitation.status)
        .select_from(User)
        .join(
            models.StaffInvitation,
            User.id == models.StaffInvitation.user_id,
            isouter=True,
        )
        .where(User.id == user_id)
    )
    return (await db_session.execute(smtm)).tuples().first()


# async def create_staff_invitation(
#     db_session: AsyncSession,
#     user_id: UserId,
#     seller_id: types.SellerId,
# ) -> None:
#     smtm = sa.insert(models.StaffInvitation).values(
#         {
#             models.StaffInvitation.user_id: user_id,
#             models.StaffInvitation.seller_id: seller_id,
#         }
#     )
#     await db_session.execute(smtm)
