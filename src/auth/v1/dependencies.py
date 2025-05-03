import logging
from typing import TypedDict, Annotated
from datetime import datetime, timezone

import jwt
from jwt.exceptions import ExpiredSignatureError, PyJWTError
from redis.asyncio import Redis
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.database import session_maker, redis_conn
from src.auth.v1 import exceptions
from src.auth.v1 import repositories
from src.auth.v1.config import auth_config
from src.auth.v1.types import UserId
from src.auth.v1.models import User
from src.common.repositories import get_value_from_cache

logger = logging.getLogger("auth")

oauth2_schema = OAuth2PasswordBearer(tokenUrl="/v1/auth/login/")


class TokenPayload(TypedDict):
    exp: int
    user_id: UserId
    is_founder: bool | None
    security_stamp: str


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


async def get_current_active_user(
    data: Annotated[TokenPayload, Depends(decode_access_token)],
    session_maker: Annotated[async_sessionmaker[AsyncSession], Depends(session_maker)],
    redis: Annotated[Redis, Depends(redis_conn)],
) -> User:
    if "user_id" not in data:
        raise exceptions.InvalidTokenExc
    user_id = data.get("user_id")
    assert user_id is not None
    security_stamp = data.get("security_stamp")  # Check security stamp validity
    if (not security_stamp) or (
        not await get_value_from_cache(
            redis, f"security-stamp:{user_id}:{security_stamp}"
        )
    ):
        raise exceptions.SecurityStampChangedExc
    async with session_maker.begin() as session:
        user = await repositories.get_user_by_id(session, user_id)
        if user is None:
            raise exceptions.InvalidTokenExc
        if not user.is_active:
            raise exceptions.AccountNotActiveExc
        return user


# async def get_current_active_founder(data: Annotated[TokenPayload, Depends(decode_access_token)]) -> bool:
#     if "user_id" not in data:
#         raise exceptions.InvalidTokenExc
#     user_id = data.get("user_id")
#     assert user_id is not None
#     async with session_maker.begin() as session:
#         user = await repositories.get_user_by_id(session, user_id)
#         if user is None:
#             raise exceptions.InvalidTokenExc
#         return user.is_founder
