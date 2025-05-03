import logging
from typing import Annotated

from fastapi import APIRouter, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.database import session_maker
from src.providers.v1 import services
from src.auth.v1.types import UserId
from src.providers.v1.types import ProviderId

logger = logging.getLogger("providers")

router = APIRouter()


# @router.post(
#     "/invite-staff/{user_id}/",
#     status_code=status.HTTP_204_NO_CONTENT,
#     responses={
#         404: {
#             "content": {"application/json": {"example": {"detail": "Staff not found."}}}
#         },
#         400: {
#             "content": {
#                 "application/json": {
#                     "examples": {
#                         "account-not-active": {
#                             "summary": "Account not active.",
#                             "value": {"detail": "This account is not active."},
#                         },
#                         "cannot-invite-sellers": {
#                             "summary": "Cannot invite sellers.",
#                             "value": {"detail": "Cannot invite providers."},
#                         },
#                         "seller-staff-unique": {
#                             "summary": "Cannot invite sellers.",
#                             "value": {
#                                 "detail": "Each provider can invite a user only once."
#                             },
#                         },
#                         "staff-already-at-work": {
#                             "summary": "Staff already at work.",
#                             "value": {
#                                 "detail": "This user is already working for another provider."
#                             },
#                         },
#                     }
#                 }
#             }
#         },
#         500: {
#             "content": {
#                 "application/json": {
#                     "example": {"detail": "Check database connection."}
#                 }
#             }
#         },
#     },
# )
# async def invite_staff(
#     session_maker: Annotated[async_sessionmaker[AsyncSession], Depends(session_maker)],
#     user_id: UserId,
# ) -> None:
#     await services.invite_staff(session_maker, ProviderId(9), user_id)
