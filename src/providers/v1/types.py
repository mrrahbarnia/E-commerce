from typing import NewType
from enum import StrEnum, auto

ProviderId = NewType("ProviderId", int)
ProviderStaffId = NewType("ProviderStaffId", int)


class InvitationStatus(StrEnum):
    PENDING = auto()
    ACCEPTED = auto()
    CANCELED = auto()
