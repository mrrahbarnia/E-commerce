from typing import NewType, TypedDict
from uuid import UUID
from enum import StrEnum, auto

from src.auth.v1.types import UserRole, UserId

ProviderId = NewType("ProviderId", UUID)
ProviderStaffId = NewType("ProviderStaffId", int)


class InvitationStatus(StrEnum):
    PENDING = auto()
    ACCEPTED = auto()
    CANCELED = auto()


# ================ Return types ================ #
class LookupForStaffReturnType(TypedDict):
    user_role: UserRole
    user_id: UserId
    username: str
    full_name: str
    avatar: str
