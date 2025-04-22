import logging

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.v1 import models
from src.auth.v1 import types
from src.common.exceptions import CheckDbConnection

logger = logging.getLogger("auth")


async def get_user_id_by_email(
    db_session: AsyncSession, email: str
) -> types.UserId | None:
    smtm = sa.select(models.UserIdentity.user_id).where(
        models.UserIdentity.identity_value == email
    )
    return await db_session.scalar(smtm)


async def get_user_id_by_phone_number(
    db_session: AsyncSession, phone_number: str
) -> types.UserId | None:
    smtm = sa.select(models.UserIdentity.user_id).where(
        models.UserIdentity.identity_value == phone_number
    )
    return await db_session.scalar(smtm)


async def create_user(db_session: AsyncSession, hashed_password: str) -> types.UserId:
    smtm = (
        sa.insert(models.User)
        .values(
            {
                models.User.role: types.UserRole.CUSTOMER,
                models.User.hashed_password: hashed_password,
            }
        )
        .returning(models.User.id)
    )
    try:
        user_id = await db_session.scalar(smtm)
        if not user_id:
            raise CheckDbConnection
        return user_id
    except Exception as ex:
        logger.error(ex)
        raise CheckDbConnection


async def create_user_identity(
    db_session: AsyncSession,
    user_id: types.UserId,
    identity_type: types.IdentityType,
    identity_value: str,
    full_name: str,
    username: str,
    avatar: str,
):
    smtm = sa.insert(models.UserIdentity).values(
        {
            models.UserIdentity.user_id: user_id,
            models.UserIdentity.identity_type: identity_type,
            models.UserIdentity.identity_value: identity_value,
            models.UserIdentity.full_name: full_name,
            models.UserIdentity.avatar: avatar,
            models.UserIdentity.username: username,
        }
    )
    try:
        await db_session.execute(smtm)
    except Exception as ex:
        logging.error(ex)
        raise CheckDbConnection
