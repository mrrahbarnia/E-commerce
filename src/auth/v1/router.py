from typing import Annotated

from redis.asyncio import Redis
from fastapi import APIRouter, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.database import session_maker, redis_conn
from src.auth.v1 import schemas
from src.auth.v1 import handlers
from src.auth.v1.config import auth_config


router = APIRouter()


@router.post(
    "/register/",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.RegisterOut,
    responses={
        201: {
            "content": {
                "application/json": {
                    "example": {"username": "test.", "identity_value": "09131111111"}
                }
            }
        },
        409: {
            "description": "Conflict due to duplication email or phone number.",
            "content": {
                "application/json": {
                    "examples": {
                        "duplicate-email": {
                            "summary": "Duplicate email",
                            "value": {"detail": "Email must be unique."},
                        },
                        "duplicate-phone-number": {
                            "summary": "Duplicate phone number",
                            "value": {"detail": "Phone number must be unique."},
                        },
                    }
                }
            },
        },
        500: {
            "content": {
                "application/json": {
                    "example": {"detail": "Check database connection."}
                }
            }
        },
    },
)
async def register(
    session_maker: Annotated[async_sessionmaker[AsyncSession], Depends(session_maker)],
    redis: Annotated[Redis, Depends(redis_conn)],
    payload: schemas.RegisterIn,
) -> dict:
    """
    - **identity type** must be "email" or "phone_number"
    - **phone number** must be exact 11 digits and unique.
    - **email** must be unique and in correct format.
    - **password** must be at least 8 chars.
    - **confirm passwords** must be match password.
    - **username** must be at least 200 chars.
    - **full_name** must be at least 200 chars.
    """
    await handlers.register_handler(session_maker, redis, payload)
    return {"username": payload.username, "identity_value": payload.identity_value}


@router.post(
    "/activate-account/",
    status_code=status.HTTP_200_OK,
    description=f"""
- ***VerificationCode*** must be exact 6 digits.
- ***Verification code*** has {auth_config.VERIFY_ACCOUNT_MESSAGE_LIFETIME_SEC} seconds life time.
    """,
    responses={
        200: {
            "content": {
                "application/json": {"example": {"detail": "Verified successfully."}}
            }
        },
        400: {
            "content": {
                "application/json": {
                    "example": {"detail": "Code might expired or invalid."}
                }
            }
        },
        500: {
            "content": {
                "application/json": {
                    "example": {"detail": "Check database connection."}
                }
            }
        },
    },
)
async def activate_account(
    session_maker: Annotated[async_sessionmaker[AsyncSession], Depends(session_maker)],
    redis: Annotated[Redis, Depends(redis_conn)],
    payload: schemas.ActivateAccount,
) -> dict:
    await handlers.activate_account(session_maker, redis, payload.verification_code)
    return {"detail": "Verified successfully."}
