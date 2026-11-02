
import pytest

from app.models import Product


@pytest.mark.asyncio
async def test_inventory_pagination_and_filtering(client, test_db):
    async with test_db() as session:
        session.add_all([
            Product(
                sku="SKU-A",
                name="Product A",
                stock_quantity=5,
                warehouse_location="WH-1",
                base_price_usd=10.0,
                is_active=True,
            ),
            Product(
                sku="SKU-B",
                name="Product B",
                stock_quantity=15,
                warehouse_location="WH-1",
                base_price_usd=20.0,
                is_active=True,
            ),
            Product(
                sku="SKU-C",
                name="Product C",
                stock_quantity=25,
                warehouse_location="WH-2",
                base_price_usd=30.0,
                is_active=True,
            ),
            Product(
                sku="SKU-D",
                name="Inactive Product",
                stock_quantity=100,
                warehouse_location="WH-2",
                base_price_usd=40.0,
                is_active=False,
            ),
        ])

        await session.commit()

    response = await client.get(
        "/api/v1/inventory?limit=1&offset=1&min_stock=10",
        headers={"X-Api-Key": "test-secret"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["pagination"]["total"] == 2
    assert data["pagination"]["limit"] == 1
    assert data["pagination"]["offset"] == 1

    assert len(data["items"]) == 1
    assert data["items"][0]["sku"] == "SKU-C"
    assert data["items"][0]["stock_quantity"] == 25

    # Inactive products must not appear.
    assert all(
        item["sku"] != "SKU-D"
        for item in data["items"]
    )
