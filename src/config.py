from typing import Any

from dotenv import load_dotenv
from pythonjsonlogger import jsonlogger  # noqa
from pydantic import BaseModel, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.constants import Environment

load_dotenv()


class CustomBaseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../.env", env_file_encoding="utf-8", extra="ignore"
    )


class Config(CustomBaseSettings):
    POSTGRES_URL: PostgresDsn
    REDIS_URL: RedisDsn
    ENVIRONMENT: Environment = Environment.PRODUCTION


settings = Config()  # type: ignore


class LogConfig(BaseModel):
    version: int = 1
    disable_existing_loggers: bool = False
    formatters: dict[str, dict[str, str]] = {
        "console": {
            "format": "%(asctime)s %(levelname)s %(module)s %(funcName)s %(message)s",
            "datefmt": "%Y-%m-%dT%H:%M:%SZ",
        },
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "fmt": "%(asctime)s %(levelname)s %(module)s %(funcName)s %(message)s",
            "datefmt": "%Y-%m-%dT%H:%M:%SZ",
        },
    }
    handlers: dict[str, dict[str, str | int]] = {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "console",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "WARNING",
            "formatter": "json",
            "filename": "/app/logs/app.log",
            "maxBytes": 5000000,  # 5 MB
            "encoding": "utf-8",
            "backupCount": 3,
        },
    }
    loggers: dict[str, dict[str, list[str] | bool | str]] = {
        "root": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "auth": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "providers": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
    }


app_configs: dict[str, Any] = {"title": "E-commerce"}

if not settings.ENVIRONMENT.is_debug:
    app_configs["openapi_url"] = None
