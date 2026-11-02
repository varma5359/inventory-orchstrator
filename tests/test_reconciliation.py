
import pytest

from fastapi import BackgroundTasks
from sqlalchemy import select
from sqlalchemy.exc import OperationalError

from app.models import Product, ReconciliationAuditLog
from app.schemas import InventoryManifestRequest
from app.routers.inventory import trigger_bulk_reconciliation
from app.services import reconciliation_worker


@pytest.mark.asyncio
async def test_reconciliation_updates_stock_and_audit(client, test_db):
    async with test_db() as session:
        session.add(
            Product(
                sku="TEST-001",
                name="Test Product",
                stock_quantity=50,
                warehouse_location="WH-1",
                base_price_usd=25.0,
                is_active=True,
            )
        )
        await session.commit()

    response = await client.post(
        "/api/v1/inventory/reconcile",
        headers={"X-Api-Key": "test-secret"},
        json={
            "manifest": [
                {
                    "sku": "TEST-001",
                    "stock_quantity": 45,
                },
                {
                    "sku": "UNKNOWN-001",
                    "stock_quantity": 120,
                },
            ]
        },
    )

    assert response.status_code == 202

    response_data = response.json()

    assert response_data["status"] == "ACCEPTED"
    assert response_data["skus_submitted"] == 2
    assert response_data["task_id"]

    # Verify actual background processing results.
    async with test_db() as session:
        product = await session.get(Product, "TEST-001")

        assert product.stock_quantity == 45

        audit_result = await session.execute(
            __import__("sqlalchemy").select(ReconciliationAuditLog)
            .order_by(ReconciliationAuditLog.id.desc())
        )

        audit = audit_result.scalars().first()

        assert audit is not None
        assert audit.status == "SUCCESS"
        assert audit.skus_processed == 1
        assert "UNKNOWN-001" in audit.error_message


@pytest.mark.asyncio
async def test_duplicate_skus_are_rejected(client):
    response = await client.post(
        "/api/v1/inventory/reconcile",
        headers={"X-Api-Key": "test-secret"},
        json={
            "manifest": [
                {"sku": "TEST-001", "stock_quantity": 10},
                {"sku": "TEST-001", "stock_quantity": 20},
            ]
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_reconciliation_is_scheduled_as_background_task():
    """Verify route schedules work rather than directly awaiting the worker."""

    request = InventoryManifestRequest(
        manifest=[
            {"sku": "TEST-001", "stock_quantity": 45}
        ]
    )

    background_tasks = BackgroundTasks()

    response = await trigger_bulk_reconciliation(
        request=request,
        background_tasks=background_tasks,
    )

    assert response["status"] == "ACCEPTED"
    assert len(background_tasks.tasks) == 1
    assert background_tasks.tasks[0].func.__name__ == (
        "process_inventory_manifest"
    )



class LockedTransaction:
    """Simulate a SQLite transaction that fails because of a lock."""

    def __init__(self, error):
        self.error = error

    async def __aenter__(self):
        raise self.error

    async def __aexit__(self, exc_type, exc_value, traceback):
        return False


class LockedSession:
    """Simulate an async database session with a locked transaction."""

    def __init__(self, error):
        self.error = error

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        return False

    def begin(self):
        return LockedTransaction(self.error)


def create_sqlite_lock_error():
    return OperationalError(
        "UPDATE products SET stock_quantity = ?",
        {},
        Exception("database is locked"),
    )


def test_sqlite_lock_error_detection():
    lock_error = create_sqlite_lock_error()

    unrelated_error = OperationalError(
        "SELECT * FROM products",
        {},
        Exception("no such table: products"),
    )

    assert reconciliation_worker.is_sqlite_lock_error(lock_error)
    assert not reconciliation_worker.is_sqlite_lock_error(
        unrelated_error
    )


@pytest.mark.asyncio
async def test_reconciliation_succeeds_after_temporary_locks(
    test_db, monkeypatch
):
    """Verify reconciliation succeeds when an early attempt is locked."""

    async with test_db() as session:
        session.add(
            Product(
                sku="RETRY-001",
                name="Retry Product",
                stock_quantity=10,
                warehouse_location="WH-1",
                base_price_usd=15.0,
                is_active=True,
            )
        )
        await session.commit()

    lock_error = create_sqlite_lock_error()
    session_calls = 0

    def session_factory():
        nonlocal session_calls
        session_calls += 1

        if session_calls <= 2:
            return LockedSession(lock_error)

        return test_db()

    monkeypatch.setattr(
        reconciliation_worker,
        "AsyncSessionLocal",
        session_factory,
    )

    await reconciliation_worker.process_inventory_manifest(
        manifest=[
            {"sku": "RETRY-001", "stock_quantity": 25}
        ],
        task_id="temporary-lock-test",
    )

    # Two locked attempts followed by one successful attempt.
    assert session_calls == 3

    async with test_db() as session:
        product = await session.get(Product, "RETRY-001")

        assert product.stock_quantity == 25

        result = await session.execute(
            select(ReconciliationAuditLog).order_by(
                ReconciliationAuditLog.id.desc()
            )
        )
        audit = result.scalars().first()

        assert audit.status == "SUCCESS"
        assert audit.skus_processed == 1


@pytest.mark.asyncio
async def test_reconciliation_records_fallback_after_three_locks(
    test_db, monkeypatch
):
    """Verify exactly three attempts and a RETRY_FALLBACK audit."""

    lock_error = create_sqlite_lock_error()
    session_calls = 0
    locked_attempts = 0

    def session_factory():
        nonlocal session_calls, locked_attempts
        session_calls += 1

        if locked_attempts < 3:
            locked_attempts += 1
            return LockedSession(lock_error)

        # The fourth session is used by record_failure()
        # to write the fallback audit record.
        return test_db()

    monkeypatch.setattr(
        reconciliation_worker,
        "AsyncSessionLocal",
        session_factory,
    )

    await reconciliation_worker.process_inventory_manifest(
        manifest=[
            {"sku": "LOCKED-001", "stock_quantity": 50}
        ],
        task_id="persistent-lock-test",
    )

    assert locked_attempts == 3
    assert session_calls == 4

    async with test_db() as session:
        result = await session.execute(
            select(ReconciliationAuditLog).order_by(
                ReconciliationAuditLog.id.desc()
            )
        )
        audit = result.scalars().first()

        assert audit is not None
        assert audit.status == "RETRY_FALLBACK"
        assert audit.skus_processed == 0
        assert "after 3 attempts" in audit.error_message
