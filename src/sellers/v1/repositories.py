import logging

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from src.sellers.v1 import models
from src.sellers.v1 import types
from src.auth.v1.types import UserId
# from src.auth.v1.models import User

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
