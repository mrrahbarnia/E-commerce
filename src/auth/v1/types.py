from uuid import UUID
from typing import NewType
from enum import StrEnum, auto

UserId = NewType("UserId", UUID)
UserIdentityId = NewType("UserIdentityId", int)
RoleId = NewType("RoleId", int)
PermissionId = NewType("PermissionId", int)


class UserRole(StrEnum):
    ADMIN = auto()
    CUSTOMER = auto()
    PROVIDER = auto()


class IdentityType(StrEnum):
    EMAIL = auto()
    PHONE_NUMBER = auto()
