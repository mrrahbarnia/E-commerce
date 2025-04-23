from pydantic_settings import BaseSettings


class AuthConfig(BaseSettings):
    PASSWORD_PATTERN: str
    EMAIL_PATTERN: str
    PHONE_NUMBER_PATTERN: str
    VERIFY_ACCOUNT_MESSAGE_LIFETIME_SEC: int


auth_config = AuthConfig()  # type: ignore
