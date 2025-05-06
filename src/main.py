import logging
from logging.config import dictConfig
from typing import AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from fastapi import FastAPI, Depends

from src.database import session_maker
from typing import Annotated
from src.config import LogConfig, app_configs
from src.auth.v1 import router as auth_router_v1
from src.providers.v1 import router as sellers_router_v1
from src.admin.v1 import router as admin_router_v1

logger = logging.getLogger("root")


@asynccontextmanager
async def lifespan(_application: FastAPI) -> AsyncGenerator:
    dictConfig(LogConfig().model_dump())
    logger.info("App is running...")
    yield


app = FastAPI(**app_configs, lifespan=lifespan)


@app.get("/")
async def root(
    session: Annotated[async_sessionmaker[AsyncSession], Depends(session_maker)],
) -> dict[str, str]:
    return {"message": "Hello World"}


app.include_router(router=auth_router_v1.router, prefix="/v1/auth", tags=["auth"])
app.include_router(router=admin_router_v1.router, prefix="/v1/admin", tags=["admin"])
# app.include_router(
#     router=sellers_router_v1.router, prefix="/v1/providers", tags=["providers"]
# )
