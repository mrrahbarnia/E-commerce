import logging
from logging.config import dictConfig
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

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

app.include_router(router=auth_router_v1.router, prefix="/v1/auth", tags=["auth"])
app.include_router(router=admin_router_v1.router, prefix="/v1/admin", tags=["admin"])
# app.include_router(
#     router=sellers_router_v1.router, prefix="/v1/providers", tags=["providers"]
# )
