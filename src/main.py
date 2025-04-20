import logging
from logging.config import dictConfig
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.config import LogConfig, app_configs

logger = logging.getLogger("root")


@asynccontextmanager
async def lifespan(_application: FastAPI) -> AsyncGenerator:
    dictConfig(LogConfig().model_dump())
    logger.info("App is running...")
    yield


app = FastAPI(**app_configs, lifespan=lifespan)


@app.get("/hello-world")
async def hello_world() -> str:
    return "Hello world..."
