
import pytest
import pytest_asyncio

from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.database import Base, get_db
from app.config import settings
from app.services import reconciliation_worker


@pytest_asyncio.fixture
async def test_db(tmp_path, monkeypatch):
    """Create an isolated temporary SQLite database for each test."""

    database_path = tmp_path / "test_inventory.db"

    test_engine = create_async_engine(
        f"sqlite+aiosqlite:///{database_path}",
        connect_args={"timeout": 30},
    )

    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    TestSessionLocal = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async def override_get_db():
        async with TestSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    # The background worker must use the same temporary database.
    monkeypatch.setattr(
        reconciliation_worker,
        "AsyncSessionLocal",
        TestSessionLocal,
    )

    yield TestSessionLocal

    app.dependency_overrides.clear()
    await test_engine.dispose()


@pytest_asyncio.fixture
async def client(test_db, monkeypatch):
    """Create an HTTP client without starting the development DB lifecycle."""

    monkeypatch.setattr(settings, "API_KEY_SECRET", "test-secret")

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as test_client:
        yield test_client
