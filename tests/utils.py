import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient, ASGITransport

from src.main import app
from src.auth.v1.models import User, UserIdentity
from src.auth.v1.types import UserRole, IdentityType
from src.auth.v1.utils import hash_password


async def create_user(
    session: AsyncSession,
    *,
    identity_value: str,
    username: str,
    full_name: str,
    password: str,
    role: UserRole,
) -> None:
    create_user_stmt = (
        sa.insert(User)
        .values(
            {
                User.role: role,
                User.hashed_password: hash_password(password),
                User.is_active: True,
            }
        )
        .returning(User.id)
    )
    user_id = await session.scalar(create_user_stmt)

    await session.execute(
        sa.insert(UserIdentity).values(
            {
                UserIdentity.identity_type: IdentityType.EMAIL,
                UserIdentity.identity_value: identity_value,
                UserIdentity.full_name: full_name,
                UserIdentity.username: username,
                UserIdentity.avatar: f"{username}.jpg",
                UserIdentity.user_id: user_id,
            }
        )
    )


async def get_authenticated_client(identity_value: str, password: str) -> AsyncClient:
    client = AsyncClient(
        transport=ASGITransport(app=app, client=("127.0.0.1", 8000)),
        base_url="http://test",
    )
    response = await client.post(
        "/v1/auth/login/", data={"username": identity_value, "password": password}
    )
    refresh_token_cookie = response.cookies.get("refresh_token")
    assert refresh_token_cookie is not None
    client.cookies.clear()
    client.cookies.set("refresh_token", refresh_token_cookie)
    client.headers.update(
        {"Authorization": f"Bearer {response.json()['access_token']}"}
    )
    return client
