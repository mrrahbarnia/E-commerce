import pytest

from httpx import AsyncClient


async def test_root(client: AsyncClient) -> None:
    json = {
        "avatar": "https://example.com/pic.jpg",
        "company_name": "Mobl Iran",
        "confirm_password": "12345678",
        "full_name": "Mohammadreza rahbarnia",
        "identity_type": "email",
        "identity_value": "user@example.com",
        "is_provider": True,
        "password": "12345678",
        "username": "mrrahbarnia",
    }
    response = await client.post("/v1/auth/register/", json=json)
    print(response.json())
    assert response.status_code == 201
