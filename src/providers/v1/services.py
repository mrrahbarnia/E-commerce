import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.providers.v1 import exceptions
from src.providers.v1 import repositories

# from src.providers.v1 import types
from src.common.exceptions import CheckDbConnection
from src.auth.v1.types import UserId, UserRole
# from src.auth.v1 import repositories as auth_repositories

logger = logging.getLogger("providers")


async def invite_staff(
    session_maker: async_sessionmaker[AsyncSession],
    inviter_id: UserId,
    user_id: UserId,
) -> None:
    try:
        async with session_maker.begin() as session:
            user_info = await repositories.check_user_status_before_invitation(
                session, user_id
            )
            if user_info is None:
                raise exceptions.UserNotFoundExc
            is_active, user_role, invitation_status = user_info
            if not is_active:
                raise exceptions.AccountNotActiveForInvitationExc
            elif user_role is UserRole.PROVIDER:
                raise exceptions.CannotInviteProviderExc
            await repositories.invitate_user(session, user_id, inviter_id)

    except exceptions.UserNotFoundExc as ex:
        logger.info(ex)
        raise ex

    except exceptions.AccountNotActiveForInvitationExc as ex:
        logger.info(ex)
        raise ex

    except exceptions.CannotInviteProviderExc as ex:
        logger.info(ex)
        raise ex

    except Exception as ex:
        if "pk_provider_invitations" in str(ex):
            logger.info(ex)
            raise exceptions.ProviderAlreadyInviteUserExc
        logger.error(ex)
        raise CheckDbConnection
