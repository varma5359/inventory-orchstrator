
import uuid

from fastapi import APIRouter, Depends, Query, BackgroundTasks, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Product
from app.schemas import InventoryManifestRequest
from app.services.reconciliation_worker import process_inventory_manifest


router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.get("")
async def get_paginated_inventory(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    min_stock: int | None = Query(default=None, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Return active inventory products with pagination and stock filtering."""

    filters = [Product.is_active.is_(True)]

    if min_stock is not None:
        filters.append(Product.stock_quantity >= min_stock)

    count_query = (
        select(func.count())
        .select_from(Product)
        .where(*filters)
    )
    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    inventory_query = (
        select(Product)
        .where(*filters)
        .order_by(Product.sku)
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(inventory_query)
    products = result.scalars().all()

    return {
        "items": [
            {
                "sku": product.sku,
                "name": product.name,
                "stock_quantity": product.stock_quantity,
                "warehouse_location": product.warehouse_location,
                "base_price_usd": product.base_price_usd,
                "is_active": product.is_active,
            }
            for product in products
        ],
        "pagination": {
            "total": total,
            "limit": limit,
            "offset": offset,
        },
    }


@router.post("/reconcile", status_code=status.HTTP_202_ACCEPTED)
async def trigger_bulk_reconciliation(
    request: InventoryManifestRequest,
    background_tasks: BackgroundTasks,
):
    """
    Accept an inventory manifest and schedule background reconciliation.
    """

    task_id = str(uuid.uuid4())

    manifest_data = [
        item.model_dump()
        for item in request.manifest
    ]

    background_tasks.add_task(
        process_inventory_manifest,
        manifest=manifest_data,
        task_id=task_id,
    )

    return {
        "task_id": task_id,
        "status": "ACCEPTED",
        "message": "Inventory reconciliation scheduled.",
        "skus_submitted": len(manifest_data),
    }
