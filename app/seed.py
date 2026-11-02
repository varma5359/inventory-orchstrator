
import asyncio
import logging

from sqlalchemy import select

from app.database import AsyncSessionLocal, init_db, close_db
from app.models import Product


logger = logging.getLogger(__name__)


SEED_PRODUCTS = [
    {
        "sku": "LAPTOP-001",
        "name": "Business Laptop",
        "stock_quantity": 50,
        "warehouse_location": "WH-MUM-01",
        "base_price_usd": 899.99,
        "is_active": True,
    },
    {
        "sku": "MOUSE-001",
        "name": "Wireless Mouse",
        "stock_quantity": 150,
        "warehouse_location": "WH-MUM-01",
        "base_price_usd": 24.99,
        "is_active": True,
    },
    {
        "sku": "KEYBOARD-001",
        "name": "Mechanical Keyboard",
        "stock_quantity": 75,
        "warehouse_location": "WH-HYD-01",
        "base_price_usd": 79.99,
        "is_active": True,
    },
    {
        "sku": "MONITOR-001",
        "name": "27-inch Monitor",
        "stock_quantity": 30,
        "warehouse_location": "WH-HYD-01",
        "base_price_usd": 249.99,
        "is_active": True,
    },
    {
        "sku": "WEBCAM-001",
        "name": "HD Webcam",
        "stock_quantity": 0,
        "warehouse_location": "WH-DEL-01",
        "base_price_usd": 59.99,
        "is_active": False,
    },
]


async def seed_database() -> None:
    """Insert missing sample products without overwriting existing data."""

    await init_db()

    try:
        async with AsyncSessionLocal() as session:
            async with session.begin():
                seed_skus = [
                    product["sku"] for product in SEED_PRODUCTS
                ]

                result = await session.execute(
                    select(Product.sku).where(
                        Product.sku.in_(seed_skus)
                    )
                )

                existing_skus = set(result.scalars().all())

                new_products = [
                    Product(**product)
                    for product in SEED_PRODUCTS
                    if product["sku"] not in existing_skus
                ]

                session.add_all(new_products)

                logger.info(
                    "Database seeding completed. inserted=%s existing=%s",
                    len(new_products),
                    len(existing_skus),
                )

    finally:
        await close_db()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    asyncio.run(seed_database())
