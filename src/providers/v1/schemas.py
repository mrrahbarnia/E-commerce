import logging

from pydantic import BaseModel

from src.auth.v1.types import UserRole, UserId

logger = logging.getLogger("sellers")


class LookupForStaffOut(BaseModel):
    user_role: UserRole
    user_id: UserId
    username: str
    full_name: str
    avatar: str
