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
from src.auth.v1.dependencies import decode_token
from src.auth.v1.config import auth_config

logger = logging.getLogger("auth")


async def register(
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


async def activate_account(
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


async def resend_verification_code(
    session_maker: async_sessionmaker[AsyncSession],
    redis: Redis,
    payload: schemas.ResendVerificationCodeIn,
):
    async with session_maker.begin() as session:
        user_info: (
            tuple[types.UserId, bool] | None
        ) = await repositories.check_user_existence_and_account_activation_status(
            db_session=session,
            identity_type=payload.identity_type(),
            identity_value=payload.identity_value,
        )
        if user_info is None:
            raise exceptions.AccountDoesntExistExc
        elif user_info[1] is True:
            raise exceptions.AccountAlreadyActivatedExc
        else:
            verification_code = utils.generate_random_code(6)
            await repositories.set_key_to_cache(
                redis,
                f"verification-code:{verification_code}",
                str(user_info[0]),
                ex=auth_config.VERIFY_ACCOUNT_MESSAGE_LIFETIME_SEC,
            )
            match payload.identity_type:
                case types.IdentityType.EMAIL:
                    utils.send_email()  # TODO: Sending email in production mode.
                case types.IdentityType.PHONE_NUMBER:
                    utils.send_sms()  # TODO: Sending SMS in production mode.


async def login(
    session_maker: async_sessionmaker[AsyncSession],
    redis: Redis,
    username: str,
    password: str,
) -> schemas.Token:
    try:
        async with session_maker.begin() as session:
            user_info = await repositories.get_user_credentials_by_identity_value(
                session, username
            )
            if (not user_info) or (not utils.verify_password(password, user_info[2])):
                raise exceptions.InvalidCredentialsExc
            elif user_info[1] is False:
                raise exceptions.AccountNotActiveExc
            else:
                access_token = utils.encode_access_token({"user_id": str(user_info[0])})
                refresh_token = utils.encode_refresh_token(
                    {"user_id": str(user_info[0])}
                )
                # Whitelisting valid refresh tokens
                await repositories.set_key_to_cache(
                    redis,
                    refresh_token,
                    str(user_info[0]),
                    auth_config.REFRESH_TOKEN_LIFE_TIME_MINUTE * 60,
                )
                return schemas.Token(
                    access_token=access_token, refresh_token=refresh_token
                )

    except exceptions.InvalidCredentialsExc as ex:
        logger.info(ex)
        raise ex

    except exceptions.AccountNotActiveExc as ex:
        logger.info(ex)
        raise ex

    except Exception as ex:
        logger.warning(ex)
        raise CheckDbConnection


async def get_refresh_token(redis: Redis, refresh_token: str) -> schemas.Token:
    if await repositories.get_del_cached_value(redis, refresh_token) is None:
        raise exceptions.InvalidTokenExc
    payload = decode_token(refresh_token)
    access_token = utils.encode_access_token({"user_id": payload["user_id"]})
    new_refresh_token = utils.encode_refresh_token({"user_id": payload["user_id"]})
    # Whitelisting valid refresh tokens
    await repositories.set_key_to_cache(
        redis,
        new_refresh_token,
        payload["user_id"],
        auth_config.REFRESH_TOKEN_LIFE_TIME_MINUTE * 60,
    )
    return schemas.Token(access_token=access_token, refresh_token=new_refresh_token)


async def logout(redis: Redis, refresh_token: str) -> None:
    await repositories.get_del_cached_value(redis, refresh_token)
