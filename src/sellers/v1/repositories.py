# import logging

# import sqlalchemy as sa
# from sqlalchemy.ext.asyncio import AsyncSession

# logger = logging.getLogger("sellers")


# async def create_seller_staff(
#     db_session: AsyncSession,
#     user_id: int,
# ) -> None:
#     smtm = sa.insert(models.SellerStaff).values(
#         {
#             models.SellerStaff.user_id: user_id,
#             models.SellerStaff.company_name: company_name,
#         }
#     )
#     try:
#         await db_session.execute(smtm)
#     except Exception as ex:
#         logger.error(ex)
#         raise CheckDbConnection
