import logging
from typing import Any

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.v1 import models
from src.auth.v1 import types
from src.common.exceptions import CheckDbConnection

logger = logging.getLogger("auth")


async def get_user_by_id(
    db_session: AsyncSession, user_id: types.UserId
) -> models.User | None:
    smtm = sa.select(models.User).where(models.User.id == user_id)
    return await db_session.scalar(smtm)


async def get_user_passwd_by_id(
    db_session: AsyncSession, user_id: types.UserId
) -> str | None:
    smtm = sa.select(models.User.hashed_password).where(models.User.id == user_id)
    return await db_session.scalar(smtm)


async def get_user_id_by_identity_value(
    db_session: AsyncSession, identity_value: str
) -> types.UserId | None:
    smtm = sa.select(models.UserIdentity.user_id).where(
        models.UserIdentity.identity_value == identity_value
    )
    return await db_session.scalar(smtm)


async def create_user(
    db_session: AsyncSession, hashed_password: str, is_provider: bool
) -> types.UserId:
    smtm = (
        sa.insert(models.User)
        .values(
            {
                models.User.role: types.UserRole.CUSTOMER
                if not is_provider
                else types.UserRole.PROVIDER,
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


async def get_user_credentials_by_identity_value(
    db_session: AsyncSession, identity_value: str
) -> tuple[types.UserId, bool, str, types.UserRole] | None:
    # SELECT u.id, u.is_active, u.hashed_password, u.role
    # FROM users u
    # JOIN user_identities ui ON u.id=ui.user_id AND ui.identity_value='user@example.com'
    smtm = (
        sa.select(
            models.User.id,
            models.User.is_active,
            models.User.hashed_password,
            models.User.role,
        )
        .select_from(models.User)
        .join(
            models.UserIdentity,
            sa.and_(
                models.User.id == models.UserIdentity.user_id,
                models.UserIdentity.identity_value == identity_value,
            ),
        )
    )
    return (await db_session.execute(smtm)).tuples().first()


# # async def get_user_roles()


async def create_user_identity(
    db_session: AsyncSession,
    user_id: types.UserId,
    identity_type: types.IdentityType,
    identity_value: str,
    full_name: str,
    username: str,
    avatar: str,
) -> None:
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
    await db_session.execute(smtm)


async def check_user_existence_and_account_activation_status(
    db_session: AsyncSession, identity_type: types.IdentityType, identity_value: Any
) -> tuple[types.UserId, bool] | None:
    smtm = (
        sa.select(models.User.id, models.User.is_active)
        .join(models.UserIdentity, models.User.id == models.UserIdentity.user_id)
        .where(
            sa.and_(
                models.UserIdentity.identity_value == identity_value,
                models.UserIdentity.identity_type == identity_type.value,
            )
        )
    )
    return (await db_session.execute(smtm)).tuples().first()


async def activate_user_account(
    db_session: AsyncSession, user_id: types.UserId
) -> None:
    smtm = (
        sa.update(models.User)
        .values({models.User.is_active: True})
        .where(models.User.id == user_id)
    )
    await db_session.execute(smtm)


async def update_user_password(
    db_session: AsyncSession, user_id: types.UserId, hashed_password: str
) -> None:
    smtm = (
        sa.update(models.User)
        .values({models.User.hashed_password: hashed_password})
        .where(models.User.id == user_id)
    )
    await db_session.execute(smtm)
