import logging
from typing import TypedDict, Annotated
from datetime import datetime, timezone

import jwt
from jwt.exceptions import ExpiredSignatureError, PyJWTError
from redis.asyncio import Redis
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from src.database import redis_conn
from src.auth.v1 import exceptions
from src.auth.v1.config import auth_config
from src.auth.v1.types import UserId, UserRole
from src.common.repositories import get_value_from_cache

logger = logging.getLogger("auth")

oauth2_schema = OAuth2PasswordBearer(tokenUrl="/v1/auth/login/")


class TokenPayload(TypedDict):
    exp: int
    user_id: UserId
    is_founder: bool | None
    security_stamp: str
    role: UserRole


def _decode_token(token: str) -> TokenPayload:
    try:
        payload: TokenPayload = jwt.decode(
            jwt=token,
            key=auth_config.SECRET_KEY,
            algorithms=[auth_config.JWT_ALGORITHM],
            options={"verify_exp": False},
        )
        exp = payload.get("exp")
        if exp is not None:
            expire_time = datetime.fromtimestamp(exp, tz=timezone.utc)
            if expire_time < datetime.now(timezone.utc):
                raise ExpiredSignatureError
        return payload
    except ExpiredSignatureError as e:
        logger.info(e)
        raise exceptions.ExpiredTokenExc
    except PyJWTError as e:
        logger.info(e)
        raise exceptions.InvalidTokenExc


def decode_access_token(
    access_token: Annotated[str, Depends(oauth2_schema)],
) -> TokenPayload:
    return _decode_token(access_token)


def decode_refresh_token(refresh_token: str) -> TokenPayload:
    return _decode_token(refresh_token)


async def check_security_stamp(
    token_data: Annotated[TokenPayload, Depends(decode_access_token)],
    redis: Annotated[Redis, Depends(redis_conn)],
) -> TokenPayload:
    if "user_id" not in token_data:
        raise exceptions.InvalidTokenExc
    user_id = token_data.get("user_id")
    assert user_id is not None
    security_stamp = token_data.get("security_stamp")  # Check security stamp validity
    if (not security_stamp) or (
        not await get_value_from_cache(
            redis, f"security-stamp:{user_id}:{security_stamp}"
        )
    ):
        raise exceptions.SecurityStampChangedExc
    return token_data


async def get_user_id(
    token_data: Annotated[TokenPayload, Depends(check_security_stamp)],
) -> UserId:
    return token_data["user_id"]


async def get_admin_id(
    token_data: Annotated[TokenPayload, Depends(check_security_stamp)],
) -> UserId:
    if token_data["role"] != UserRole.ADMIN:
        raise exceptions.OnlyAdminCanAccessExc
    return token_data["user_id"]
