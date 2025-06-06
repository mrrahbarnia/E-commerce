import re
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator, BeforeValidator

from src.auth.v1 import types
from src.auth.v1 import validators
from src.auth.v1.config import auth_config


class RegisterOut(BaseModel):
    username: Annotated[str, Field(max_length=200)]
    identity_value: str


class RegisterIn(RegisterOut):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "identity_type": "email",
                    "identity_value": "user@example.com",
                    "password": "12345678",
                    "confirm_password": "12345678",
                    "full_name": "Mohammadreza rahbarnia",
                    "username": "mrrahbarnia",
                    "avatar": "https://example.com/pic.jpg",
                    "is_provider": True,
                    "company_name": "Mobl Iran",
                }
            ]
        }
    )
    identity_type: types.IdentityType
    identity_value: str
    password: str
    confirm_password: str
    full_name: Annotated[str, Field(max_length=200)]
    avatar: Annotated[str, Field(max_length=200)]
    is_provider: bool | None = None
    company_name: Annotated[str | None, Field(max_length=200)] = None

    @model_validator(mode="after")
    def validate_model(self):
        validators.validate_password(self.password)
        validators.validate_passwords_match(self.password, self.confirm_password)
        validators.validate_identity_value_based_on_identity_type(
            self.identity_type, self.identity_value
        )
        validators.ensure_enter_company_name_for_providers(
            self.is_provider, self.company_name
        )

        return self


class ActivateAccountIn(BaseModel):
    verification_code: Annotated[str, Field(max_length=6)]


class IdentityValueIn(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "identity_value": "user@example.com",
                }
            ]
        }
    )
    identity_value: Annotated[
        str, BeforeValidator(validators.ensure_identity_value_format)
    ]

    def identity_type(self) -> types.IdentityType:
        if re.fullmatch(auth_config.PHONE_NUMBER_PATTERN, self.identity_value):
            return types.IdentityType.PHONE_NUMBER
        return types.IdentityType.EMAIL


class Token(BaseModel):
    access_token: str
    refresh_token: str


class ChangePasswordIn(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "old_password": "12345678",
                    "new_password": "123456789",
                    "confirm_password": "123456789",
                }
            ]
        }
    )
    old_password: str
    new_password: str
    confirm_password: str

    @model_validator(mode="after")
    def validate_model(self):
        validators.validate_password(self.new_password)
        validators.validate_passwords_match(self.new_password, self.confirm_password)
        return self


class ChangePasswordOut(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2V"}
            ]
        }
    )
    access_token: str


# class UsersOut(BaseModel):
#     id: types.UserId
#     username: str
#     identity_value: str
#     role: types.UserRole
#     is_active: bool
#     registered_at: str
#     permissions: list[str]
#     company_name: str
#     is_founder: bool
