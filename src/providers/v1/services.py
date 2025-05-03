import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.providers.v1 import exceptions
from src.providers.v1 import repositories
from src.providers.v1 import types
from src.common.exceptions import CheckDbConnection
from src.auth.v1.types import UserId, UserRole
from src.auth.v1 import repositories as auth_repositories

logger = logging.getLogger("providers")


# async def invite_staff(
#     session_maker: async_sessionmaker[AsyncSession],
#     provider_id: types.ProviderId,
#     user_id: UserId,
# ) -> None:
#     try:
#         async with session_maker.begin() as session:
#             user_info = await repositories.check_staff_status_before_invitation(
#                 session, user_id
#             )
#             if user_info is None:
#                 raise exceptions.StaffNotFoundExc
#             is_active, user_role, invitation_status = user_info
#             if not is_active:
#                 raise exceptions.AccountNotActiveForInvitationExc
#             elif user_role is UserRole.PROVIDER:
#                 raise exceptions.CannotInviteSellerExc
#             await repositories.create_staff_invitation(session, user_id, seller_id)

#     except exceptions.StaffNotFoundExc as ex:
#         logger.info(ex)
#         raise ex

#     except exceptions.AccountNotActiveForInvitationExc as ex:
#         logger.info(ex)
#         raise ex

#     except exceptions.CannotInviteSellerExc as ex:
#         logger.info(ex)
#         raise ex

#     except Exception as ex:
#         if "pk_staff_invitations" in str(ex):
#             logger.warning(ex)
#             raise exceptions.SellerStaffUniqueExc
#         logger.error(ex)
#         raise CheckDbConnection
