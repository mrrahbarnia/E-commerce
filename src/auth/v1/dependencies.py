import logging
from datetime import datetime, timezone

import jwt
from jwt.exceptions import ExpiredSignatureError, PyJWTError
from fastapi.security import OAuth2PasswordBearer

from src.auth.v1 import exceptions
from src.auth.v1.config import auth_config

logger = logging.getLogger("auth")

oauth2_schema = OAuth2PasswordBearer(tokenUrl="/v1/auth/login/")


def decode_token(token: str) -> dict:
    try:
        payload: dict = jwt.decode(
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
