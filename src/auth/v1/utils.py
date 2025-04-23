import logging
from typing import Any
from uuid import uuid4
import secrets
from datetime import datetime, timezone, timedelta

import jwt

# from jwt.exceptions import ExpiredSignatureError,
from passlib.context import CryptContext  # type: ignore

from src.auth.v1.config import auth_config

logger = logging.getLogger("auth")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def generate_random_code(length: int) -> str:
    return str(int(uuid4()))[:length]


def send_sms():
    logger.warning("Sending sms.")


def send_email():
    logger.warning("Sending email.")


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def encode_access_token(payload: dict[str, Any]) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=auth_config.ACCESS_TOKEN_LIFE_TIME_MINUTE
    )
    payload.update({"exp": expire})
    return jwt.encode(
        payload, auth_config.SECRET_KEY, algorithm=auth_config.JWT_ALGORITHM
    )


def encode_refresh_token(payload: dict[str, Any]) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=auth_config.REFRESH_TOKEN_LIFE_TIME_MINUTE
    )
    payload.update({"exp": expire})
    return jwt.encode(
        payload, auth_config.SECRET_KEY, algorithm=auth_config.JWT_ALGORITHM
    )


# def decode(token: str) -> dict:
#     try:
#         result: dict = jwt.decode(
#             token, auth_config.SECRET_KEY, algorithms=[auth_config.JWT_ALGORITHM]
#         )
#         exp = result.get("exp")
#         if exp and datetime.fromtimestamp(exp) < datetime.now(timezone.utc):
#             raise ExpiredSignatureError
#         return result
#     except ExpiredSignatureError as exception:
#         raise JWTExpiredError() from exception
#     except JWTError as exception:
#         raise JWTDecodeError() from exception
