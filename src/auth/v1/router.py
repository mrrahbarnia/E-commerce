from typing import Annotated

from fastapi import APIRouter, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.database import session_maker, redis_conn
from src.auth.v1 import schemas
from src.auth.v1 import handlers


router = APIRouter()


@router.post(
    "/register", status_code=status.HTTP_201_CREATED, response_model=schemas.RegisterOut
)
async def register(
    session_maker: Annotated[async_sessionmaker[AsyncSession], Depends(session_maker)],
    payload: schemas.RegisterIn,
) -> dict:
    await handlers.register_handler(session_maker, payload)
    return {"username": payload.username, "identity_value": payload.identity_value}
