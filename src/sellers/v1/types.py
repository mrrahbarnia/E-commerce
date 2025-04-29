from typing import NewType
from enum import StrEnum, auto

SellerId = NewType("SellerId", int)
SellerStaffId = NewType("SellerStaffId", int)


class InvitationStatus(StrEnum):
    PENDING = auto()
    ACCEPTED = auto()
    CANCELED = auto()
