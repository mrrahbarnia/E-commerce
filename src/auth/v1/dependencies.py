import logging
from typing import TypedDict, Annotated
from datetime import datetime, timezone

import jwt
from jwt.exceptions import ExpiredSignatureError, PyJWTError
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.database import session_maker
from src.auth.v1 import exceptions
from src.auth.v1 import repositories
from src.auth.v1.config import auth_config
from src.auth.v1.types import UserId
from src.auth.v1.models import User

logger = logging.getLogger("auth")

oauth2_schema = OAuth2PasswordBearer(tokenUrl="/v1/auth/login/")


class TokenPayload(TypedDict):
    exp: int
    user_id: UserId
    security_stamp: str


def decode_token(token: str) -> TokenPayload:
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


async def get_current_active_user(
    data: Annotated[TokenPayload, Depends(decode_token)],
    session_maker: Annotated[async_sessionmaker[AsyncSession], Depends(session_maker)],
) -> User:
    if "user_id" not in data:
        raise exceptions.InvalidTokenExc
    user_id = data.get("user_id")
    assert user_id is not None
    async with session_maker.begin() as session:
        user = await repositories.get_user_by_id(session, user_id)
        if user is None:
            raise exceptions.InvalidTokenExc
        if not user.is_active:
            raise exceptions.AccountNotActiveExc
        return user
