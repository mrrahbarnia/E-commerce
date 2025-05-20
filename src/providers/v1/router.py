import logging
from typing import Annotated

from fastapi import APIRouter, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.database import session_maker
from src.providers.v1 import services
from src.providers.v1 import schemas
from src.auth.v1.types import UserId
from src.auth.v1.models import User
from src.auth.v1.dependencies import get_provider_id
from src.providers.v1.types import ProviderId

logger = logging.getLogger("providers")

router = APIRouter()


@router.post(
    "/invite-staff/{user_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {
            "content": {
                "application/json": {"example": {"detail": "Account not found."}}
            }
        },
        400: {
            "content": {
                "application/json": {
                    "examples": {
                        "account-not-active": {
                            "summary": "Account not active.",
                            "value": {"detail": "This account is not active."},
                        },
                        "cannot-invite-sellers": {
                            "summary": "Cannot invite sellers.",
                            "value": {"detail": "Cannot invite providers."},
                        },
                        "seller-staff-unique": {
                            "summary": "provider staff unique together.",
                            "value": {
                                "detail": "Each provider can invite a user only once."
                            },
                        },
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
async def invite_staff(
    session_maker: Annotated[async_sessionmaker[AsyncSession], Depends(session_maker)],
    inviter_id: Annotated[UserId, Depends(get_provider_id)],
    user_id: UserId,
) -> None:
    """
    Founders and hiring managers can add staff to their companies.
    """
    await services.invite_staff(session_maker, inviter_id, user_id)


@router.get(
    "/lookup-staff/{invitation_code}/",
    status_code=status.HTTP_200_OK,
    response_model=schemas.LookupForStaffOut,
    responses={
        404: {
            "content": {
                "application/json": {"example": {"detail": "Account not found."}}
            }
        },
        403: {
            "content": {
                "application/json": {
                    "example": {"detail": "Cannot lookup for admin users."}
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
async def lookup_for_staff(
    session_maker: Annotated[async_sessionmaker[AsyncSession], Depends(session_maker)],
    inviter_id: Annotated[UserId, Depends(get_provider_id)],
    invitation_code: str,
):
    return await services.lookup_for_staff(session_maker, invitation_code)
