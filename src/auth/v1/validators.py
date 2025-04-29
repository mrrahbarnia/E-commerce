import re

from src.auth.v1 import types
from src.auth.v1.config import auth_config


def validate_passwords_matchness(password: str, confirm_password: str) -> None:
    if password != confirm_password:
        raise ValueError("Passwords don't match!")


def validate_password(password: str) -> None:
    if not re.match(auth_config.PASSWORD_PATTERN, password):
        raise ValueError("Password must contain at least 8 chars!")


def validate_identity_value_based_on_identity_type(
    identity_type: types.IdentityType, identity_value: str
) -> None:
    if identity_type.value == types.IdentityType.EMAIL.value:
        if not re.match(auth_config.EMAIL_PATTERN, identity_value):
            raise ValueError("Email format is not correct!")
    elif identity_type.value == types.IdentityType.PHONE_NUMBER.value:
        if not re.match(auth_config.PHONE_NUMBER_PATTERN, identity_value):
            raise ValueError("Phone number must be exact 11 digits!")


def ensure_enter_company_name_for_sellers(
    is_seller: bool | None, company_name: str | None
) -> None:
    if is_seller and not company_name:
        raise ValueError("Sellers must enter their company name.")
    elif not is_seller and company_name:
        raise ValueError("Company name must be empty for non-sellers.")


def ensure_identity_value_format(value: str) -> str:
    match value:
        case v if re.fullmatch(auth_config.PHONE_NUMBER_PATTERN, v) or re.fullmatch(
            auth_config.EMAIL_PATTERN, v
        ):
            return v
        case _:
            raise ValueError("Invalid identity_value format.")
