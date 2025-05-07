import pytest
from httpx import AsyncClient


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

    # Second registration - same company name
    payload["identity_value"] = "provider2@example.com"
    payload["username"] = "providertwo"
    payload["avatar"] = "https://example.com/pic2.jpg"

    second = await client.post("/v1/auth/register/", json=payload)
    assert second.status_code == 409
    assert "Company name must be unique" in second.text
