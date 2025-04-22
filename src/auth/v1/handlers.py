import logging
from typing import assert_never

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.common.exceptions import CheckDbConnection
from src.auth.v1 import schemas
from src.auth.v1 import services
from src.auth.v1 import types
from src.auth.v1 import repositories
from src.auth.v1 import exceptions
from src.auth.v1.utils import hash_password

logger = logging.getLogger("auth")


async def register_handler(
    session_maker: async_sessionmaker[AsyncSession], payload: schemas.RegisterIn
) -> None:
    try:
        async with session_maker.begin() as session:
            match payload.identity_type:
                case types.IdentityType.EMAIL:
                    services.register_service(
                        await repositories.get_user_id_by_email(
                            session, payload.identity_value
                        ),
                        types.IdentityType.EMAIL,
                    )
                case types.IdentityType.PHONE_NUMBER:
                    services.register_service(
                        await repositories.get_user_id_by_phone_number(
                            session, payload.identity_value
                        ),
                        types.IdentityType.PHONE_NUMBER,
                    )
                case _:
                    assert_never(payload.identity_type)
            user_id = await repositories.create_user(  # Side effects: CheckDbConnection
                session, hash_password(payload.password)
            )
            await repositories.create_user_identity(  # Side effects: CheckDbConnection
                db_session=session,
                user_id=user_id,
                identity_type=payload.identity_type,
                identity_value=payload.identity_value,
                full_name=payload.full_name,
                username=payload.username,
                avatar=payload.avatar,
            )

    except exceptions.DuplicateEmailExc as ex:
        logger.info(ex)
        raise ex

    except exceptions.DuplicatePhoneNumberExc as ex:
        logger.info(ex)
        raise ex

    except Exception as ex:
        logger.exception(ex)
        raise CheckDbConnection
