from src.auth.v1 import types
from src.auth.v1 import exceptions


def register_service(
    existence_user: types.UserId | None, identity_type: types.IdentityType
) -> None:
    if existence_user and identity_type.value == types.IdentityType.EMAIL:
        raise exceptions.DuplicateEmailExc
    elif existence_user and identity_type.value == types.IdentityType.PHONE_NUMBER:
        raise exceptions.DuplicatePhoneNumberExc
