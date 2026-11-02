
import pytest


@pytest.mark.asyncio
async def test_missing_api_key_returns_401(client):
    response = await client.get("/api/v1/inventory")

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing API key."


@pytest.mark.asyncio
async def test_invalid_api_key_returns_401(client):
    response = await client.get(
        "/api/v1/inventory",
        headers={"X-Api-Key": "wrong-secret"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_valid_api_key_allows_request(client):
    response = await client.get(
        "/api/v1/inventory",
        headers={"X-Api-Key": "test-secret"},
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_endpoint_is_public(client):
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
