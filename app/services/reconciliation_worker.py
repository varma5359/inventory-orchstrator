
import asyncio
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import OperationalError

from app.database import AsyncSessionLocal
from app.models import Product, ReconciliationAuditLog


logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 3


def is_sqlite_lock_error(error: OperationalError) -> bool:
    """Identify SQLite database locking or busy errors."""
    message = str(error).lower()

    return any(
        phrase in message
        for phrase in (
            "database is locked",
            "database table is locked",
            "database is busy",
        )
    )


async def record_failure(
    status: str,
    skus_processed: int,
    error_message: str,
    task_id: str,
) -> None:
    """Write a failure or retry-exhaustion audit record."""

    try:
        async with AsyncSessionLocal() as session:
            async with session.begin():
                session.add(
                    ReconciliationAuditLog(
                        status=status,
                        skus_processed=skus_processed,
                        error_message=error_message[:4000],
                    )
                )

    except Exception:
        logger.exception(
            "Unable to save reconciliation audit record. task_id=%s",
            task_id,
        )


async def process_inventory_manifest(
    manifest: list[dict[str, Any]],
    task_id: str,
) -> None:
    """
    Reconcile inventory in the background.

    Matching products are updated atomically.
    Unknown SKUs are recorded as mismatches.
    SQLite locking errors receive up to three total attempts.
    """

    submitted_skus = [item["sku"] for item in manifest]
    last_lock_error: OperationalError | None = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            async with AsyncSessionLocal() as session:
                async with session.begin():

                    result = await session.execute(
                        select(Product).where(
                            Product.sku.in_(submitted_skus)
                        )
                    )

                    products = {
                        product.sku: product
                        for product in result.scalars().all()
                    }

                    updated_count = 0
                    unknown_skus = []

                    for item in manifest:
                        product = products.get(item["sku"])

                        if product is None:
                            unknown_skus.append(item["sku"])
                            continue

                        product.stock_quantity = item["stock_quantity"]
                        updated_count += 1

                    mismatch_message = None

                    if unknown_skus:
                        mismatch_message = (
                            "Unknown SKUs: " + ", ".join(unknown_skus)
                        )

                    # The audit and product updates share one transaction.
                    session.add(
                        ReconciliationAuditLog(
                            status="SUCCESS",
                            skus_processed=updated_count,
                            error_message=(
                                mismatch_message[:4000]
                                if mismatch_message
                                else None
                            ),
                        )
                    )

            logger.info(
                "Reconciliation completed. task_id=%s "
                "processed=%s mismatches=%s attempt=%s",
                task_id,
                updated_count,
                len(unknown_skus),
                attempt,
            )
            return

        except OperationalError as exc:
            if not is_sqlite_lock_error(exc):
                logger.exception(
                    "Database error during reconciliation. task_id=%s",
                    task_id,
                )

                await record_failure(
                    status="FAILED",
                    skus_processed=0,
                    error_message=str(exc),
                    task_id=task_id,
                )
                return

            last_lock_error = exc

            logger.warning(
                "SQLite lock encountered. task_id=%s attempt=%s/%s",
                task_id,
                attempt,
                MAX_ATTEMPTS,
            )

            if attempt < MAX_ATTEMPTS:
                await asyncio.sleep(0.1 * attempt)

        except Exception as exc:
            logger.exception(
                "Reconciliation failed. task_id=%s",
                task_id,
            )

            await record_failure(
                status="FAILED",
                skus_processed=0,
                error_message=str(exc),
                task_id=task_id,
            )
            return

    # All three attempts failed due to SQLite locking.
    await record_failure(
        status="RETRY_FALLBACK",
        skus_processed=0,
        error_message=(
            f"SQLite locking persisted after {MAX_ATTEMPTS} attempts: "
            f"{last_lock_error}"
        ),
        task_id=task_id,
    )

    logger.error(
        "Reconciliation exhausted retry attempts. task_id=%s",
        task_id,
    )
