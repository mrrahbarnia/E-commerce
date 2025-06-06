from uuid import uuid4

import pytest
from httpx import AsyncClient
from redis.asyncio import Redis

from src.auth.v1.utils import encode_token

from src.auth.v1.types import UserId, UserRole


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient, redis_client: Redis):
    payload = {
        "identity_type": "email",
        "identity_value": "testuser@example.com",
        "password": "strongPass123",
        "confirm_password": "strongPass123",
        "full_name": "Test User",
        "username": "testuser",
        "avatar": "https://example.com/avatar.jpg",
        "is_provider": True,
        "company_name": "Test Company",
    }

    response = await client.post("/v1/auth/register/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "testuser"
    assert data["identity_value"] == "testuser@example.com"
    # Deleting keys from redis memory
    keys = await redis_client.keys("verification-code:*")
    if keys:
        await redis_client.delete(*keys)


@pytest.mark.asyncio
@pytest.mark.parametrize("identity_value", ["bademail.com", "123456"])
async def test_invalid_identity_format(client: AsyncClient, identity_value: str):
    payload = {
        "identity_type": "email",
        "identity_value": identity_value,
        "password": "validpass123",
        "confirm_password": "validpass123",
        "full_name": "Invalid Email User",
        "username": "invalidemail",
        "avatar": "https://example.com/pic.jpg",
        "is_provider": False,
    }

    response = await client.post("/v1/auth/register/", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_passwords_do_not_match(client: AsyncClient):
    payload = {
        "identity_type": "email",
        "identity_value": "testmismatch@example.com",
        "password": "pass1234",
        "confirm_password": "pass12345",
        "full_name": "Mismatch User",
        "username": "mismatchuser",
        "avatar": "https://example.com/pic.jpg",
        "is_provider": False,
    }

    response = await client.post("/v1/auth/register/", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_missing_company_name_for_provider(client: AsyncClient):
    payload = {
        "identity_type": "phone_number",
        "identity_value": "09131234567",
        "password": "pass1234",
        "confirm_password": "pass1234",
        "full_name": "No Company User",
        "username": "nouser",
        "avatar": "https://example.com/pic.jpg",
        "is_provider": True,
        "company_name": None,
    }

    response = await client.post("/v1/auth/register/", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_conflict_on_duplicate_identity(client: AsyncClient, redis_client: Redis):
    # First registration
    payload = {
        "identity_type": "email",
        "identity_value": "duplicatef@example.com",
        "password": "pass1234",
        "confirm_password": "pass1234",
        "full_name": "First User",
        "username": "firstuser",
        "avatar": "https://example.com/pic.jpg",
    }

    first = await client.post("/v1/auth/register/", json=payload)
    assert first.status_code == 201

    # Second registration with same identity_value
    payload["username"] = "anotheruser"  # change username
    response = await client.post("/v1/auth/register/", json=payload)
    assert response.status_code == 409
    assert (
        "Email must be unique" in response.text
        or "Phone number must be unique" in response.text
    )
    # Deleting keys from redis memory
    keys = await redis_client.keys("verification-code:*")
    if keys:
        await redis_client.delete(*keys)


@pytest.mark.asyncio
async def test_conflict_on_duplicate_company_name(
    client: AsyncClient, redis_client: Redis
):
    payload = {
        "identity_type": "email",
        "identity_value": "provider1@example.com",
        "password": "pass1234",
        "confirm_password": "pass1234",
        "full_name": "Provider One",
        "username": "providerone",
        "avatar": "https://example.com/pic1.jpg",
        "is_provider": True,
        "company_name": "DuplicateCompany",
    }

    # First registration - should succeed
    first = await client.post("/v1/auth/register/", json=payload)
    assert first.status_code == 201

    # Second registration - same company name - should raise exc
    payload["identity_value"] = "provider2@example.com"

    second = await client.post("/v1/auth/register/", json=payload)
    assert second.status_code == 409
    assert "Company name must be unique" in second.text

    # Deleting keys from redis memory
    keys = await redis_client.keys("verification-code:*")
    if keys:
        await redis_client.delete(*keys)


@pytest.mark.asyncio
async def test_activate_account_success_after_register(
    client: AsyncClient, redis_client: Redis
):
    # Step 1: Register the user
    payload = {
        "identity_type": "email",
        "identity_value": "activate@example.com",
        "password": "strongPass123",
        "confirm_password": "strongPass123",
        "full_name": "To Be Activated",
        "username": "toactivate",
        "avatar": "https://example.com/avatar.jpg",
        "is_provider": True,
        "company_name": "ActivationCo",
    }

    register_response = await client.post("/v1/auth/register/", json=payload)
    assert register_response.status_code == 201

    # Step 2: Get verification code from Redis
    keys: list[str] = await redis_client.keys("verification-code:*")
    assert keys, "No verification code found in Redis"

    code = (keys[0].split(":"))[1]

    # Step 3: Activate the account using the retrieved code
    response = await client.post(
        "/v1/auth/activate-account/",
        json={"verification_code": code},
    )

    assert response.status_code == 200
    assert response.json() == {"detail": "Verified successfully."}


@pytest.mark.asyncio
async def test_activate_account_failure_expired_or_wrong_code(
    client: AsyncClient, redis_client: Redis
):
    fake_code = "123456"
    await redis_client.delete(
        f"verification-code:{fake_code}"
    )  # Ensure it's not in Redis

    response = await client.post(
        "/v1/auth/activate-account/",
        json={"verification_code": fake_code},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Code might expired or invalid."}


@pytest.mark.asyncio
async def test_activate_account_failure_invalid_format(client: AsyncClient):
    # Send a code that's not 6 digits
    response = await client.post(
        "/v1/auth/activate-account/",
        json={"verification_code": "abc1234"},
    )

    assert response.status_code == 422  # FastAPI's validation error


@pytest.mark.asyncio
async def test_resend_verification_code_success(client: AsyncClient):
    # First, register user
    payload = {
        "identity_type": "email",
        "identity_value": "resend@example.com",
        "password": "testpass123",
        "confirm_password": "testpass123",
        "full_name": "Resend User",
        "username": "resenduser",
        "avatar": "https://example.com/avatar.jpg",
        "is_provider": False,
        "company_name": None,
    }
    register_resp = await client.post("/v1/auth/register/", json=payload)
    assert register_resp.status_code == 201

    # Now resend verification code
    response = await client.post(
        "/v1/auth/verification-code/resend/",
        json={"identity_value": "resend@example.com"},
    )

    assert response.status_code == 200
    assert response.json() == {"detail": "Resent successfully."}


@pytest.mark.asyncio
async def test_resend_verification_code_user_not_found(client: AsyncClient):
    response = await client.post(
        "/v1/auth/verification-code/resend/",
        json={"identity_value": "notfound@example.com"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "There is no account with the provided info."}


@pytest.mark.asyncio
async def test_resend_verification_code_already_activated(client: AsyncClient):
    response = await client.post(
        "/v1/auth/verification-code/resend/",
        json={"identity_value": "activate@example.com"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Account has already been activated."}


@pytest.mark.asyncio
async def test_resend_verification_code_invalid_format(client: AsyncClient):
    response = await client.post(
        "/v1/auth/verification-code/resend/",
        json={"identity_value": "not-an-email"},
    )

    assert response.status_code == 422  # Pydantic validation error


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    # Login with correct credentials
    login_data = {
        "username": "activate@example.com",  # Using identity_value as username field in OAuth2PasswordRequestForm
        "password": "strongPass123",
    }

    response = await client.post("/v1/auth/login/", data=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data

    # Check refresh token in cookies
    assert "set-cookie" in response.headers
    cookies = response.headers["set-cookie"]
    assert "refresh_token=" in cookies


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient, redis_client: Redis):
    # Login with correct credentials
    login_data = {
        "username": "activate@example.com",  # Using identity_value as username field in OAuth2PasswordRequestForm
        "password": "strongPass1234",
    }

    response = await client.post("/v1/auth/login/", data=login_data)
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials."}


@pytest.mark.asyncio
async def test_refresh_token_success(client: AsyncClient, redis_client: Redis):
    user_id = "123"
    security_stamp = "stamp123"
    old_refresh_token = await encode_token(
        token_type="refresh_token",
        user_id=UserId(uuid4()),
        security_stamp=security_stamp,
        role=UserRole.CUSTOMER,
    )

    await redis_client.set(old_refresh_token, user_id)

    response = await client.post(
        "/v1/auth/refresh-token/",
        cookies={"refresh_token": old_refresh_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data

    # check Redis contains new refresh token
    assert await redis_client.get(data["access_token"]) is None


@pytest.mark.asyncio
async def test_refresh_token_missing_cookie(client: AsyncClient):
    client.cookies.clear()
    response = await client.post("/v1/auth/refresh-token/")
    assert response.status_code == 401
    assert response.json()["detail"] == "Token is invalid."


@pytest.mark.asyncio
async def test_refresh_token_invalid(client: AsyncClient):
    fake_token = await encode_token(
        token_type="refresh_token",
        user_id=UserId(uuid4()),
        security_stamp="fake",
        role=UserRole.CUSTOMER,
    )
    response = await client.post(
        "/v1/auth/refresh-token/",
        cookies={"refresh_token": fake_token},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Token is invalid."


@pytest.mark.asyncio
async def test_reset_password_success(client: AsyncClient):
    response = await client.put(
        "/v1/auth/reset-password/", json={"identity_value": "activate@example.com"}
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_reset_password_account_not_exists(client: AsyncClient):
    response = await client.put(
        "/v1/auth/reset-password/", json={"identity_value": "notexists@example.com"}
    )
    assert response.json() == {"detail": "There is no account with the provided info."}
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_change_password_wrong_old_password(
    authenticated_client_as_customer: AsyncClient,
):
    payload = {
        "old_password": "123456789",
        "new_password": "123456789",
        "confirm_password": "123456789",
    }
    response = await authenticated_client_as_customer.put(
        "/v1/auth/change-password/", json=payload
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Old password is incorrect."}


@pytest.mark.asyncio
async def test_change_password_passwords_dont_match(
    authenticated_client_as_customer: AsyncClient,
):
    payload = {
        "old_password": "12345678",
        "new_password": "123456789",
        "confirm_password": "1234567891",
    }
    response = await authenticated_client_as_customer.put(
        "/v1/auth/change-password/", json=payload
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_change_password_success(
    authenticated_client_as_customer: AsyncClient,
):
    payload = {
        "old_password": "12345678",
        "new_password": "123456789",
        "confirm_password": "123456789",
    }
    response = await authenticated_client_as_customer.put(
        "/v1/auth/change-password/", json=payload
    )
    assert response.status_code == 200
    assert "access_token" in response.text
