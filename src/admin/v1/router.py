import logging
from typing import Annotated

from fastapi import APIRouter, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.database import session_maker
from src.admin.v1 import services
from src.auth.v1.dependencies import get_admin_user
from src.auth.v1.models import User
from src.providers.v1.types import ProviderId

logger = logging.getLogger("admin")

router = APIRouter()


@router.put(
    "/verify-provider/{provider_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        403: {
            "content": {
                "application/json": {
                    "examples": {
                        "security-stamp": {
                            "value": {"detail": "Security stamp changed,login again."},
                        },
                        "not-admin-user": {
                            "value": {
                                "detail": "Only admin users can access this resource."
                            },
                        },
                    }
                }
            },
        },
        401: {
            "content": {
                "application/json": {"example": {"detail": "Token is invalid."}}
            }
        },
        400: {
            "content": {
                "application/json": {
                    "example": {"detail": "Provider is already active."}
                }
            }
        },
        404: {
            "content": {
                "application/json": {
                    "example": {
                        "detail": "There is no provider with the provided info."
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
async def verify_provider(
    provider_id: ProviderId,
    admin_user: Annotated[User, Depends(get_admin_user)],
    session_maker: Annotated[async_sessionmaker[AsyncSession], Depends(session_maker)],
) -> None:
    await services.verify_provider(session_maker, provider_id)
