import logging
from typing import Annotated

from fastapi import APIRouter, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.database import session_maker

logger = logging.getLogger("sellers")

router = APIRouter()


@router.post("/add-member/{user_id}/", status_code=status.HTTP_201_CREATED)
async def add_member(
    user_id: int,
    session_maker: Annotated[async_sessionmaker[AsyncSession], Depends(session_maker)],
): ...
