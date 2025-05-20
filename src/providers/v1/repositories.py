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


async def check_user_status_before_invitation(
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


async def invitate_user(
    db_session: AsyncSession,
    user_id: UserId,
    inviter_id: UserId,
) -> None:
    # INSERT INTO provider_invitations(user_id, provider_id, sent_at, status)
    # SELECT
    #     'ac146686-b4f7-4b53-9536-6331bb9b1484'::UUID,
    #     provider_id,
    #     '2000-02-02'::DATE,
    #     'PENDING'
    # FROM provider_staff
    # WHERE user_id='a712fd8f-7950-491b-bab4-b82ab23a8a6a'::UUID
    smtm = sa.insert(models.ProviderInvitation).from_select(
        [models.ProviderInvitation.user_id, models.ProviderInvitation.provider_id],
        sa.select(sa.literal(user_id), models.ProviderStaff.provider_id).where(
            models.ProviderStaff.user_id == inviter_id
        ),
    )
    await db_session.execute(smtm)
