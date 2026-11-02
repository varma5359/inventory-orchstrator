
import asyncio

import httpx

from app.main import app
from app.config import settings


async def main():

    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test"
    ) as client:

        # Test 1: Public health endpoint
        response = await client.get("/health")

        print("Health:", response.status_code)
        assert response.status_code == 200

        # Test 2: Missing API key
        response = await client.get("/api/v1/inventory")

        print("Missing key:", response.status_code)
        assert response.status_code == 401

        # Test 3: Incorrect API key
        response = await client.get(
            "/api/v1/inventory",
            headers={"X-Api-Key": "wrong-key"},
        )

        print("Incorrect key:", response.status_code)
        assert response.status_code == 401

        # Test 4: Correct API key
        response = await client.get(
            "/api/v1/inventory",
            headers={
                "X-Api-Key": settings.API_KEY_SECRET
            },
        )

        print("Correct key:", response.status_code)

        # The inventory endpoint is not implemented yet.
        # 501 proves that authentication passed through.
        assert response.status_code == 501

        print("\nAll security tests passed!")


if __name__ == "__main__":
    asyncio.run(main())
