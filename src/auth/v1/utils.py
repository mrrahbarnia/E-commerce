import logging
from uuid import uuid4

from passlib.context import CryptContext  # type: ignore

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
