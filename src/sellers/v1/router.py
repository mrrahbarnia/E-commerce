import logging
from typing import Annotated

from fastapi import APIRouter, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.database import session_maker
from src.sellers.v1 import services
from src.auth.v1.types import UserId
from src.sellers.v1.types import SellerId

logger = logging.getLogger("sellers")

router = APIRouter()


# @router.post(
#     "/add-staff/{user_id}/",
#     status_code=status.HTTP_204_NO_CONTENT,
#     responses={
#         404: {
#             "content": {"application/json": {"example": {"detail": "Staff not found."}}}
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
# async def add_staff(
#     session_maker: Annotated[async_sessionmaker[AsyncSession], Depends(session_maker)],
#     user_id: UserId | None = None,
# ) -> None:
#     await services.add_staff(session_maker, SellerId(1), user_id)
