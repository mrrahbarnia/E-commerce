import logging

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from src.sellers.v1 import models
from src.sellers.v1 import types
from src.auth.v1.types import UserId, UserRole
from src.auth.v1.models import User

logger = logging.getLogger("sellers")


async def create_seller_staff(
    db_session: AsyncSession,
    seller_id: types.SellerId,
    user_id: UserId,
) -> None:
    smtm = sa.insert(models.SellerStaff).values(
        {
            models.SellerStaff.seller_id: seller_id,
            models.SellerStaff.user_id: user_id,
        }
    )
    await db_session.execute(smtm)


async def create_seller(
    db_session: AsyncSession, user_id: UserId, company_name: str
) -> None:
    smtm = sa.insert(models.Seller).values(
        {
            models.Seller.user_id: user_id,
            models.Seller.company_name: company_name,
            models.Seller.is_founder: True,
        }
    )
    await db_session.execute(smtm)


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


async def create_staff_invitation(
    db_session: AsyncSession,
    user_id: UserId,
    seller_id: types.SellerId,
) -> None:
    smtm = sa.insert(models.StaffInvitation).values(
        {
            models.StaffInvitation.user_id: user_id,
            models.StaffInvitation.seller_id: seller_id,
        }
    )
    await db_session.execute(smtm)
