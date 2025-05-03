from typing import NewType
from uuid import UUID
from enum import StrEnum, auto

ProviderId = NewType("ProviderId", UUID)
ProviderStaffId = NewType("ProviderStaffId", int)


class InvitationStatus(StrEnum):
    PENDING = auto()
    ACCEPTED = auto()
    CANCELED = auto()
