from typing import Annotated

from pydantic import BaseModel, ConfigDict, model_validator, Field

from src.auth.v1 import types
from src.auth.v1 import validators


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

    @model_validator(mode="after")
    def validate_model(self):
        validators.validate_password(self.password)
        validators.validate_passwords_matchness(self.password, self.confirm_password)
        validators.validate_identity_value_based_on_identity_type(
            self.identity_type, self.identity_value
        )

        return self


class ActivateAccount(BaseModel):
    verification_code: Annotated[str, Field(max_length=6)]
