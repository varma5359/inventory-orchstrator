
# Stage 1: Build application dependencies
FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

RUN python -m venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

COPY requirements-runtime.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements-runtime.txt


# Stage 2: Minimal application runtime
FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Create a non-root application user and persistent data directory.
RUN groupadd --system app \
    && useradd --system --gid app --home-dir /app app \
    && mkdir -p /app /data \
    && chown -R app:app /app /data

# Copy only the installed runtime environment from the builder.
COPY --from=builder /opt/venv /opt/venv

# Copy application source code.
COPY --chown=app:app app/ ./app/

# SQLite database will be stored in the mounted /data directory.
ENV DATABASE_URL="sqlite+aiosqlite:////data/enterprise_inventory.db"

USER app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
