import pytest

# from httpx import AsyncClient

# from async_asgi_testclient import TestClient  # type: ignore
from fastapi.testclient import TestClient  # type: ignore
# import json
# from testcontsainers.postgres import PostgresContainer  # type: ignore[import]


# @pytest.mark.asyncio
# async def test_check(async_engine):
#     assert 1 == 1


# @pytest.mark.asyncio
# def test_register(client: TestClient) -> None:
#     j = {"identity_value": "user@example.com"}
#     response = client.post("/v1/auth/verification-code/resend/", json=j)
#     print(response.json())
#     assert response.status_code == 404


def test_root(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    print(response.json())
    assert response.json() == {"message": "Hello World"}
