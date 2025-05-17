import pytest
from httpx import AsyncClient
from redis.asyncio import Redis


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
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
async def test_conflict_on_duplicate_identity(client: AsyncClient):
    # First registration
    payload = {
        "identity_type": "email",
        "identity_value": "duplicate@example.com",
        "password": "pass1234",
        "confirm_password": "pass1234",
        "full_name": "First User",
        "username": "firstuser",
        "avatar": "https://example.com/pic.jpg",
        "is_provider": False,
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


@pytest.mark.asyncio
async def test_conflict_on_duplicate_company_name(client: AsyncClient):
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
    keys = await redis_client.keys("verification-code:*")
    assert keys, "No verification code found in Redis"

    # Get the most recent verification code that contains the expected identity (optional filter)
    matched_key = None
    for key in keys:
        if isinstance(key, bytes):
            key = key.decode()

        # Optionally: ensure it relates to this specific user
        # Skip this if your keys are just "verification-code:<code>" with no email inside
        if "activate" in key or True:
            matched_key = key
            break

    assert matched_key is not None, "Couldn't find a matching verification-code key"
    code = matched_key.split(":")[1]

    # Step 3: Activate the account using the retrieved code
    response = await client.post(
        "/v1/auth/activate-account/",
        json={"verification_code": code},
    )

    assert response.status_code == 200
    assert response.json() == {"detail": "Verified successfully."}

    # Step 4: Ensure Redis key is removed
    assert await redis_client.get(matched_key) is None


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
