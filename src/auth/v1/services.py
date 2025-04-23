import logging
from typing import assert_never

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.common.exceptions import CheckDbConnection
from src.auth.v1 import schemas
from src.auth.v1 import types
from src.auth.v1 import repositories
from src.auth.v1 import exceptions
from src.auth.v1 import utils
from src.auth.v1.config import auth_config

logger = logging.getLogger("auth")


async def register_handler(
    session_maker: async_sessionmaker[AsyncSession],
    redis: Redis,
    payload: schemas.RegisterIn,
) -> None:
    try:
        async with session_maker.begin() as session:
            match payload.identity_type:
                case types.IdentityType.EMAIL:
                    if await repositories.get_user_id_by_email(
                        session, payload.identity_value
                    ):
                        raise exceptions.DuplicateEmailExc
                case types.IdentityType.PHONE_NUMBER:
                    if await repositories.get_user_id_by_phone_number(
                        session, payload.identity_value
                    ):
                        raise exceptions.DuplicatePhoneNumberExc
                case _:
                    assert_never(payload.identity_type)
            user_id = await repositories.create_user(  # Side effects: CheckDbConnection
                session, utils.hash_password(payload.password)
            )
            await repositories.create_user_identity(  # Side effects: CheckDbConnection
                db_session=session,
                user_id=user_id,
                identity_type=payload.identity_type,
                identity_value=payload.identity_value,
                full_name=payload.full_name,
                username=payload.username,
                avatar=payload.avatar,
            )
        verification_code = utils.generate_random_code(6)
        await repositories.set_key_to_cache(
            redis=redis,
            name=f"verification-code:{verification_code}",
            value=str(user_id),
            ex=auth_config.VERIFY_ACCOUNT_MESSAGE_LIFETIME_SEC,
        )

    except exceptions.DuplicateEmailExc as ex:
        logger.info(ex)
        raise ex

    except exceptions.DuplicatePhoneNumberExc as ex:
        logger.info(ex)
        raise ex

    except Exception as ex:
        logger.exception(ex)
        raise CheckDbConnection


async def activate_account_handler(
    session_maker: async_sessionmaker[AsyncSession],
    redis: Redis,
    verification_code: str,
):
    user_id = await repositories.get_del_cached_value(
        redis=redis, name=f"verification-code:{verification_code}"
    )
    try:
        if user_id is None:
            raise exceptions.InvalidVerificationCodeExc
        async with session_maker.begin() as session:
            await repositories.activate_user_account(session, types.UserId(user_id))

    except exceptions.InvalidVerificationCodeExc as ex:
        logger.info(ex)
        raise ex

    except Exception as ex:
        logger.warning(ex)
        raise CheckDbConnection


async def resend_verification_code_handler(
    session_maker: async_sessionmaker[AsyncSession],
    redis: Redis,
    payload: schemas.ResendVerificationCodeIn,
):
    async with session_maker.begin() as session:
        is_active: (
            bool | None
        ) = await repositories.check_user_existence_and_account_activation_status(
            db_session=session,
            identity_type=payload.identity_type(),
            identity_value=payload.identity_value,
        )
        if is_active is None:
            raise exceptions.AccountDoesntExistExc
        elif is_active:
            raise exceptions.AccountAlreadyActivatedExc
        else:
            match payload.identity_type:
                case types.IdentityType.EMAIL:
                    utils.send_email()
                case types.IdentityType.PHONE_NUMBER:
                    utils.send_sms()
