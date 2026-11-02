
import time
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from app.config import settings
from app.database import init_db, close_db
from app.routers import inventory
from app.middleware import APIKeyMiddleware


logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format=(
        '{"timestamp": "%(asctime)s", '
        '"level": "%(levelname)s", '
        '"message": "%(message)s"}'
    ),
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown resources."""

    await init_db()
    logging.info("Application started and database initialized.")

    try:
        yield
    finally:
        await close_db()
        logging.info("Application database connections closed.")


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(APIKeyMiddleware)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)

    process_time_ms = int(
        (time.perf_counter() - start_time) * 1000
    )

    response.headers["X-Response-Time-Ms"] = str(process_time_ms)

    return response


app.include_router(inventory.router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
