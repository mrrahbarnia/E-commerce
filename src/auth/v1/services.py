import logging
from typing import assert_never

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from fastapi import HTTPException

from src.auth.v1 import schemas
from src.auth.v1 import types
from src.auth.v1 import repositories
from src.auth.v1 import exceptions
from src.auth.v1 import utils
from src.auth.v1.dependencies import decode_refresh_token
from src.auth.v1.config import auth_config
from src.providers.v1 import repositories as provider_repositories
from src.providers.v1.types import ProviderId
from src.common.exceptions import CheckDbConnection
from src.common.repositories import (
    set_key_to_cache,
    get_del_cached_value,
    del_cache_key_by_regex_pattern,
)

logger = logging.getLogger("auth")


async def register(
    session_maker: async_sessionmaker[AsyncSession],
    redis: Redis,
    payload: schemas.RegisterIn,
) -> None:
    try:
        async with session_maker.begin() as session:
            user_id: (
                types.UserId | None
            ) = await repositories.get_user_id_by_identity_value(
                session, payload.identity_value
            )
            match payload.identity_type:
                case types.IdentityType.EMAIL:
                    if user_id:
                        raise exceptions.DuplicateEmailExc
                case types.IdentityType.PHONE_NUMBER:
                    if user_id:
                        raise exceptions.DuplicatePhoneNumberExc
                case _:
                    assert_never(payload.identity_type)
            user_id = await repositories.create_user(  # Side effects: CheckDbConnection
                session,
                utils.hash_password(payload.password),
                True if payload.is_provider else False,
            )
            await repositories.create_user_identity(
                db_session=session,
                user_id=user_id,
                identity_type=payload.identity_type,
                identity_value=payload.identity_value,
                full_name=payload.full_name,
                username=payload.username,
                avatar=payload.avatar,
            )
            if payload.is_provider:
                assert (
                    payload.company_name is not None
                )  # Because of validator layer on top of schemas.
                provider_id: (
                    ProviderId | None
                ) = await provider_repositories.create_provider(
                    session, payload.company_name
                )
                if not provider_id:
                    raise CheckDbConnection
                await provider_repositories.create_provider_staff(
                    db_session=session,
                    provider_id=provider_id,
                    user_id=user_id,
                    is_founder=True,
                )
        verification_code = utils.generate_random_code(6)
        await set_key_to_cache(
            redis=redis,
            name=f"verification-code:{verification_code}",
            value=str(user_id),
            ex=auth_config.VERIFY_ACCOUNT_MESSAGE_LIFETIME_SEC,
        )
        # TODO: Sending email or sms in production mode.

    except exceptions.DuplicateEmailExc as ex:
        logger.info(ex)
        raise ex

    except exceptions.DuplicatePhoneNumberExc as ex:
        logger.info(ex)
        raise ex

    except Exception as ex:
        if "uq_providers_name" in str(ex):
            logger.info(ex)
            raise exceptions.DuplicateCompanyNameExc
        logger.exception(ex)
        raise CheckDbConnection


async def activate_account(
    session_maker: async_sessionmaker[AsyncSession],
    redis: Redis,
    verification_code: str,
) -> None:
    user_id = await get_del_cached_value(
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
    payload: schemas.IdentityValueIn,
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
            await set_key_to_cache(
                redis,
                f"verification-code:{verification_code}",
                str(user_info[0]),
                ex=auth_config.VERIFY_ACCOUNT_MESSAGE_LIFETIME_SEC,
            )
            match payload.identity_type:
                case types.IdentityType.EMAIL:
                    utils.send_email(
                        verification_code
                    )  # TODO: Sending email in production mode.
                case types.IdentityType.PHONE_NUMBER:
                    utils.send_sms(
                        verification_code
                    )  # TODO: Sending SMS in production mode.


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
            if not user_info:
                raise exceptions.InvalidCredentialsExc

            user_id, is_active, hashed_password, role = user_info
            # if role == types.UserRole.SELLER:
            #     raise exceptions.SellerAccountExc

            if not utils.verify_password(password, hashed_password):
                raise exceptions.InvalidCredentialsExc

            elif is_active is False:
                raise exceptions.AccountNotActiveExc

            else:
                # Generating security stamp, storing it in cache and decoding it into the access token.
                security_stamp = utils.generate_security_stamp()
                await set_key_to_cache(
                    redis,
                    f"security-stamp:{user_id}:{security_stamp}",
                    str(user_id),
                    auth_config.ACCESS_TOKEN_LIFE_TIME_MINUTE * 60,
                )
                access_token = await utils.encode_token(
                    token_type="access_token",
                    user_id=user_id,
                    security_stamp=security_stamp,
                    role=role,
                )

                refresh_token = await utils.encode_token(
                    token_type="refresh_token",
                    user_id=user_id,
                    security_stamp=security_stamp,
                    role=role,
                )
                # Whitelisting valid refresh tokens
                await set_key_to_cache(
                    redis,
                    refresh_token,
                    str(user_id),
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


async def get_refresh_token(redis: Redis, refresh_token: str | None) -> schemas.Token:
    try:
        if (
            not refresh_token
            or await get_del_cached_value(redis, refresh_token) is None
        ):
            raise exceptions.InvalidTokenExc
        payload = decode_refresh_token(refresh_token)
        # Generating security stamp, storing it in cache and decoding it into the access token.
        await set_key_to_cache(
            redis,
            f"security-stamp:{payload['user_id']}:{payload['security_stamp']}",
            str(payload["user_id"]),
            auth_config.ACCESS_TOKEN_LIFE_TIME_MINUTE * 60,
        )
        access_token = await utils.encode_token(
            token_type="access_token",
            user_id=payload["user_id"],
            security_stamp=payload["security_stamp"],
            role=payload["role"],
        )

        # Generating new refresh token and storing it in cache.
        new_refresh_token = await utils.encode_token(
            token_type="refresh_token",
            user_id=payload["user_id"],
            security_stamp=payload["security_stamp"],
            role=payload["role"],
        )
        # Whitelisting valid refresh tokens
        await set_key_to_cache(
            redis,
            new_refresh_token,
            str(payload["user_id"]),
            auth_config.REFRESH_TOKEN_LIFE_TIME_MINUTE * 60,
        )
        return schemas.Token(access_token=access_token, refresh_token=new_refresh_token)

    except exceptions.InvalidTokenExc as ex:
        logger.warning(ex)
        raise ex

    except Exception as ex:
        logger.warning(ex)
        raise CheckDbConnection


async def logout(redis: Redis, refresh_token: str) -> None:
    await get_del_cached_value(
        redis, refresh_token
    )  # Deleting refresh token from cache.
    payload = decode_refresh_token(refresh_token)
    await get_del_cached_value(
        redis, f"security-stamp:{payload['user_id']}:{payload['security_stamp']}"
    )  # Deleting security stamp from cache.


async def reset_password(
    session_maker: async_sessionmaker[AsyncSession],
    redis: Redis,
    payload: schemas.IdentityValueIn,
) -> None:
    try:
        async with session_maker.begin() as session:
            user_id: (
                types.UserId | None
            ) = await repositories.get_user_id_by_identity_value(
                session, payload.identity_value
            )
            if not user_id:
                raise exceptions.AccountDoesntExistExc
            new_password = utils.generate_random_code(8)
            new_hashed_password = utils.hash_password(new_password)
            await repositories.update_user_password(
                session, user_id, new_hashed_password
            )
            match payload.identity_type():
                case types.IdentityType.EMAIL:
                    utils.send_email(new_password)
                case types.IdentityType.PHONE_NUMBER:
                    utils.send_sms(new_password)
                case _:
                    assert_never(payload.identity_type())

            # Deleting security stamp from cache.
            await del_cache_key_by_regex_pattern(
                redis,
                f"security-stamp:{user_id}:*",
            )

    except exceptions.AccountDoesntExistExc as ex:
        logger.info(ex)
        raise ex

    except Exception as ex:
        logger.warning(ex)
        raise CheckDbConnection


async def change_password(
    session_maker: async_sessionmaker[AsyncSession],
    redis: Redis,
    user_id: types.UserId,
    payload: schemas.ChangePasswordIn,
    refresh_token: str,
) -> schemas.Token:
    try:
        async with session_maker.begin() as session:
            hashed_password = await repositories.get_user_passwd_by_id(session, user_id)
            if not hashed_password:
                raise HTTPException(
                    status_code=500,
                    detail="Unexpected error",
                )

            if not utils.verify_password(payload.old_password, hashed_password):
                raise exceptions.WrongOldPasswordExc

            new_hashed_password = utils.hash_password(payload.new_password)
            await repositories.update_user_password(
                session, user_id, new_hashed_password
            )

            # Regenerating security stamp, storing it in cache, deleting previous security stamp and decoding it into the access token and refresh token.
            await del_cache_key_by_regex_pattern(
                redis,
                f"security-stamp:{user_id}:*",
            )
            await get_del_cached_value(redis, refresh_token)
            new_security_stamp = utils.generate_security_stamp()
            await set_key_to_cache(
                redis,
                f"security-stamp:{user_id}:{new_security_stamp}",
                str(user_id),
                auth_config.ACCESS_TOKEN_LIFE_TIME_MINUTE * 60,
            )
            decoded_refresh_token = decode_refresh_token(refresh_token)
            access_token = await utils.encode_token(
                token_type="access_token",
                user_id=user_id,
                security_stamp=new_security_stamp,
                role=decoded_refresh_token["role"],
            )
            refresh_token = await utils.encode_token(
                token_type="refresh_token",
                user_id=user_id,
                security_stamp=new_security_stamp,
                role=decoded_refresh_token["role"],
            )
            await set_key_to_cache(
                redis,
                refresh_token,
                str(user_id),
                auth_config.REFRESH_TOKEN_LIFE_TIME_MINUTE * 60,
            )
            return schemas.Token(access_token=access_token, refresh_token=refresh_token)

    except exceptions.WrongOldPasswordExc as ex:
        logger.info(ex)
        raise ex

    except Exception as ex:
        logger.warning(ex)
        raise CheckDbConnection
