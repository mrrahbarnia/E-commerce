from pydantic_settings import BaseSettings


class AuthConfig(BaseSettings):
    PASSWORD_PATTERN: str
    EMAIL_PATTERN: str
    PHONE_NUMBER_PATTERN: str
    VERIFY_ACCOUNT_MESSAGE_LIFETIME_SEC: int
    SECRET_KEY: str
    ACCESS_TOKEN_LIFE_TIME_MINUTE: int
    REFRESH_TOKEN_LIFE_TIME_MINUTE: int
    JWT_ALGORITHM: str


auth_config = AuthConfig()  # type: ignore
