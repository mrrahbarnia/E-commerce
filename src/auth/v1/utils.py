import logging
import secrets
from typing import Literal
from uuid import uuid4
from datetime import datetime, timezone, timedelta

import jwt
from passlib.context import CryptContext  # type: ignore

from src.auth.v1.types import UserId, UserRole
from src.auth.v1.config import auth_config

logger = logging.getLogger("auth")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def generate_random_code(length: int) -> str:
    return str(int(uuid4()))[:length]


def generate_security_stamp() -> str:
    return secrets.token_urlsafe(8)


def send_sms(content: str):
    logger.critical(f"Sending sms. {content}")


def send_email(content: str):
    logger.critical(f"Sending email. {content}")


async def encode_token(
    token_type: Literal["access_token", "refresh_token"],
    user_id: UserId,
    security_stamp: str | None,
    role: UserRole,
) -> str:
    if security_stamp is None:
        security_stamp = generate_security_stamp()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=auth_config.ACCESS_TOKEN_LIFE_TIME_MINUTE
        if token_type == "access_token"
        else auth_config.REFRESH_TOKEN_LIFE_TIME_MINUTE
    )
    payload = {
        "user_id": str(user_id),
        "security_stamp": security_stamp,
        "role": str(role),
        "exp": expire,
    }
    return jwt.encode(
        payload, auth_config.SECRET_KEY, algorithm=auth_config.JWT_ALGORITHM
    )
