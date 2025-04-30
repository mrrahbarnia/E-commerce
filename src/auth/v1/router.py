from typing import Annotated

from redis.asyncio import Redis
from fastapi import APIRouter, Response, status, Depends, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.config import settings
from src.database import session_maker, redis_conn
from src.auth.v1 import schemas
from src.auth.v1 import services
from src.auth.v1.config import auth_config
from src.auth.v1.models import User
from src.auth.v1.dependencies import get_current_active_user

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
                        "duplicate-company-name": {
                            "summary": "Duplicate company name",
                            "value": {"detail": "Company name must be unique."},
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
    - **company_name** If is_seller is set to true then company_name is mandatory and must at least 200 chars.
    """
    await services.register(session_maker, redis, payload)
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
    payload: schemas.ActivateAccountIn,
) -> dict:
    await services.activate_account(session_maker, redis, payload.verification_code)
    return {"detail": "Verified successfully."}


@router.post(
    "/verification-code/resend/",
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "content": {
                "application/json": {"example": {"detail": "Resent successfully."}}
            }
        },
        404: {
            "content": {
                "application/json": {
                    "example": {"detail": "There is no account with the provided info."}
                }
            }
        },
        401: {
            "description": "The user has been already activated.",
            "content": {
                "application/json": {
                    "example": {"detail": "Account has already been activated."}
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
async def resend_verification_code(
    session_maker: Annotated[async_sessionmaker[AsyncSession], Depends(session_maker)],
    redis: Annotated[Redis, Depends(redis_conn)],
    payload: schemas.IdentityValueIn,
) -> dict:
    """
    - **identity value** must be in correct format.
    """
    await services.resend_verification_code(session_maker, redis, payload)
    return {"detail": "Resent successfully."}


@router.post(
    "/login/",
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2V"
                    }
                }
            }
        },
        401: {
            "content": {
                "application/json": {"example": {"detail": "Invalid credentials."}}
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
async def login(
    response: Response,
    session_maker: Annotated[async_sessionmaker[AsyncSession], Depends(session_maker)],
    redis: Annotated[Redis, Depends(redis_conn)],
    payload: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> dict:
    tokens = await services.login(
        session_maker, redis, payload.username, payload.password
    )
    response.set_cookie(
        key="refresh_token",
        value=tokens.refresh_token,
        httponly=True,
        secure=True if settings.ENVIRONMENT == "PRODUCTION" else False,
        samesite="strict" if settings.ENVIRONMENT == "PRODUCTION" else "none",
        max_age=auth_config.REFRESH_TOKEN_LIFE_TIME_MINUTE * 60,
        path="/",
    )
    return {"access_token": tokens.access_token}


@router.post(
    "/refresh-token/",
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2V"
                    }
                }
            }
        },
        401: {
            "content": {
                "application/json": {
                    "examples": {
                        "invalid-token": {
                            "summary": "Invalid token",
                            "value": {"detail": "Token is invalid."},
                        },
                        "expired-token": {
                            "summary": "Expired token",
                            "value": {"detail": "Token has been expired."},
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
async def get_refresh_token(
    response: Response,
    redis: Annotated[Redis, Depends(redis_conn)],
    refresh_token: str = Cookie(None),
) -> dict:
    tokens = await services.get_refresh_token(redis, refresh_token)
    response.set_cookie(
        key="refresh_token",
        value=tokens.refresh_token,
        httponly=True,
        secure=True if settings.ENVIRONMENT == "PRODUCTION" else False,
        samesite="strict" if settings.ENVIRONMENT == "PRODUCTION" else "none",
        max_age=auth_config.REFRESH_TOKEN_LIFE_TIME_MINUTE * 60,
        path="/",
    )
    return {"access_token": tokens.access_token}


@router.get("/logout/", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    redis: Annotated[Redis, Depends(redis_conn)], refresh_token: str = Cookie(None)
) -> None:
    await services.logout(redis, refresh_token)


@router.put(
    "/reset-password/",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "There is no account with the provided info."
                    }
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
async def reset_password(
    session_maker: Annotated[async_sessionmaker[AsyncSession], Depends(session_maker)],
    redis: Annotated[Redis, Depends(redis_conn)],
    payload: schemas.IdentityValueIn,
) -> None:
    await services.reset_password(session_maker, redis, payload)


@router.put(
    "/change-password/",
    status_code=status.HTTP_200_OK,
    # response_model=schemas.ChangePasswordOut,
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2V"
                    }
                }
            }
        },
        400: {
            "content": {
                "application/json": {
                    "example": {"access_token": "Old password is incorrect."}
                }
            }
        },
        403: {
            "content": {
                "application/json": {
                    "example": {"detail": "Security stamp changed,login again."}
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
async def change_password(
    response: Response,
    session_maker: Annotated[async_sessionmaker[AsyncSession], Depends(session_maker)],
    redis: Annotated[Redis, Depends(redis_conn)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    payload: schemas.ChangePasswordIn,
    refresh_token: str = Cookie(None),
):
    print(refresh_token)
    return "OK"
    # tokens = await services.change_password(
    #     session_maker, redis, current_user.id, payload, refresh_token
    # )
    # response.set_cookie(
    #     key="refresh_token",
    #     value=tokens.refresh_token,
    #     httponly=True,
    #     secure=True if settings.ENVIRONMENT == "PRODUCTION" else False,
    #     samesite="strict" if settings.ENVIRONMENT == "PRODUCTION" else "none",
    #     max_age=auth_config.REFRESH_TOKEN_LIFE_TIME_MINUTE * 60,
    #     path="/",
    # )
    # return {"access_token": tokens.access_token}
