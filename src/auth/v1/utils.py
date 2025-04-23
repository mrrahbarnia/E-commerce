from uuid import uuid4

from passlib.context import CryptContext  # type: ignore

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def generate_random_code(length: int) -> str:
    return str(int(uuid4()))[:length]
