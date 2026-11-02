
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy import event

from app.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args={
        "timeout": 30,
    },
)


@event.listens_for(engine.sync_engine, "connect")
def configure_sqlite_connection(dbapi_connection, connection_record):
    """
    Configure SQLite connection-level settings.
    """

    cursor = dbapi_connection.cursor()

    try:
        cursor.execute("PRAGMA busy_timeout = 30000")
        cursor.execute("PRAGMA foreign_keys = ON")
    finally:
        cursor.close()


Base = declarative_base()


AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db():
    """
    Provides an asynchronous database session.

    Transaction ownership belongs to the service or API
    operation that performs the database modification.
    """

    async with AsyncSessionLocal() as session:
        try:
            yield session

        except Exception:
            await session.rollback()
            raise

async def init_db():
    """
    Initialize SQLite and create registered database tables.
    """

    # Import models to register them with SQLAlchemy metadata.
    from app import models  # noqa: F401

    async with engine.begin() as connection:

        # Enable Write-Ahead Logging for file-based SQLite.
        await connection.exec_driver_sql(
            "PRAGMA journal_mode=WAL"
        )

        await connection.run_sync(Base.metadata.create_all)


async def close_db():
    """
    Dispose of database connections during application shutdown.
    """

    await engine.dispose()
