# Enterprise Inventory Orchestrator

An asynchronous inventory management and reconciliation service built using **Python, FastAPI, SQLAlchemy, SQLite, and Docker**.

The application provides secure inventory APIs, background stock reconciliation, audit logging, pagination, filtering, and retry handling for SQLite database locks.

---

## 1. Project Overview

### What is an Inventory Orchestrator?

An Inventory Orchestrator is a backend service that manages inventory information and synchronizes stock quantities using incoming inventory manifests.

For example, an organization may maintain inventory across multiple warehouses. An external inventory system periodically sends a manifest containing product SKUs and their latest stock quantities.

The orchestrator receives this information, identifies matching products, updates their stock quantities, and records an audit trail of the reconciliation operation.

### Main Objectives

- Maintain product inventory in a centralized database.
- Provide secure REST APIs for inventory access.
- Support asynchronous inventory reconciliation.
- Update stock quantities using SKU matching.
- Identify and record unknown SKUs.
- Maintain an audit history of reconciliation operations.
- Handle temporary SQLite database locking.
- Support Docker-based deployment with persistent storage.

### Example Business Scenario

Suppose the existing inventory database contains:

| SKU | Product | Existing stock |
|---|---|---:|
| LAPTOP-001 | Business Laptop | 50 |
| MOUSE-001 | Wireless Mouse | 150 |
| KEYBOARD-001 | Mechanical Keyboard | 75 |

An external warehouse system sends:

```json
{
  "manifest": [
    {
      "sku": "LAPTOP-001",
      "stock_quantity": 60
    },
    {
      "sku": "MOUSE-001",
      "stock_quantity": 100
    },
    {
      "sku": "UNKNOWN-001",
      "stock_quantity": 25
    }
  ]
}
```

The orchestrator:

1. Matches the submitted SKUs against existing products.
2. Updates the laptop stock from 50 to 60.
3. Updates the mouse stock from 150 to 100.
4. Identifies `UNKNOWN-001` as an unknown SKU.
5. Does not insert the unknown product.
6. Records the reconciliation result in the audit table.

---

## 2. Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.13 | Backend programming language |
| FastAPI | REST API development |
| Pydantic | Request validation and data schemas |
| SQLAlchemy 2.x | ORM and database transactions |
| aiosqlite | Asynchronous SQLite database driver |
| SQLite | Persistent relational database |
| Uvicorn | ASGI application server |
| asyncio | Asynchronous execution |
| FastAPI BackgroundTasks | Background reconciliation execution |
| pytest | Automated testing |
| pytest-asyncio | Asynchronous test execution |
| HTTPX | API testing |
| Docker | Application containerization |
| Docker Compose | Container orchestration |

### Why These Technologies?

**FastAPI**

FastAPI provides asynchronous endpoint support, request validation, dependency injection, and automatic API schema generation.

**SQLAlchemy**

SQLAlchemy provides ORM models, database queries, transaction management, and asynchronous database sessions.

**SQLite**

SQLite provides lightweight relational database storage without requiring a separate database server.

**aiosqlite**

aiosqlite allows SQLite operations to be used through Python's asynchronous database interface.

**Docker**

Docker packages the application and its runtime dependencies into a reproducible container environment.

---

## 3. System Architecture

```text
                 External Inventory System
                            |
                            |
                    Inventory Manifest
                            |
                            v
                  FastAPI Application
                            |
                            v
                   API Key Middleware
                            |
                            v
                    Request Validation
                            |
              +-------------+-------------+
              |                           |
              v                           v
       Inventory API              Reconciliation API
              |                           |
              v                           v
       SQLAlchemy ORM             HTTP 202 Accepted
              |                           |
              v                           v
           SQLite                 BackgroundTasks
                                          |
                                          v
                                Reconciliation Worker
                                          |
                              +-----------+-----------+
                              |                       |
                              v                       v
                         SKU Matching             Unknown SKUs
                              |                       |
                              v                       v
                         Stock Updates           Audit Details
                              |
                              v
                       Database Transaction
                              |
                              v
                       Audit Log Recording
```

### Architecture Explanation

1. The client sends an HTTP request.
2. API key middleware verifies authentication.
3. FastAPI validates the request payload.
4. The inventory router handles the requested operation.
5. SQLAlchemy communicates with SQLite.
6. Reconciliation requests are scheduled using BackgroundTasks.
7. The reconciliation worker processes submitted SKUs.
8. Database changes and successful audit records are committed transactionally.
9. Errors and retry outcomes are recorded in the audit table where possible.

---

## 4. Project Structure

```text
inventory-orchstrator/
│
├── app/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── middleware.py
│   ├── models.py
│   ├── schemas.py
│   ├── seed.py
│   │
│   ├── routers/
│   │   ├── inventory.py
│   │   └── ...
│   │
│   └── services/
│       ├── reconciliation_worker.py
│       └── ...
│
├── tests/
│   ├── conftest.py
│   ├── test_middleware.py
│   ├── test_inventory.py
│   └── test_reconciliation.py
│
├── .env
├── .env.example
├── .dockerignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── requirements-runtime.txt
├── pytest.ini
├── instructions.md
└── README.md
```

### Important Files

| File | Responsibility |
|---|---|
| `main.py` | Application initialization and lifespan |
| `config.py` | Environment-based configuration |
| `database.py` | Async engine, sessions, and schema initialization |
| `middleware.py` | API key authentication |
| `models.py` | SQLAlchemy database models |
| `schemas.py` | Pydantic request validation |
| `seed.py` | Initial sample database records |
| `routers/inventory.py` | Inventory and reconciliation endpoints |
| `services/reconciliation_worker.py` | Background reconciliation logic |
| `tests/` | Automated test suite |
| `Dockerfile` | Multi-stage container image |
| `docker-compose.yml` | Container configuration and persistent volume |

---

## 5. Database Design

The application uses SQLite with SQLAlchemy ORM.

### Product Model

The Product model represents inventory records.

| Column | Type | Description |
|---|---|---|
| sku | String(100) | Unique product identifier and primary key |
| name | String(255) | Product name |
| stock_quantity | Integer | Available stock |
| warehouse_location | String(255) | Warehouse identifier |
| base_price_usd | Float | Product base price in USD |
| is_active | Boolean | Whether the product is active |

**Database constraints:**

- SKU is the primary key.
- Product name cannot be null.
- Stock quantity cannot be negative.
- Base price cannot be negative.
- Active status defaults to `True`.

### ReconciliationAuditLog Model

This model stores the results of inventory reconciliation operations.

| Column | Type | Description |
|---|---|---|
| id | Integer | Primary key |
| timestamp | DateTime | Reconciliation timestamp |
| status | String(30) | Reconciliation result |
| skus_processed | Integer | Number of matched SKUs processed |
| error_message | Text | Optional error or unknown SKU information |

### Supported Audit Statuses

| Status | Meaning |
|---|---|
| SUCCESS | Reconciliation completed successfully |
| RETRY_FALLBACK | SQLite lock retries were exhausted |
| FAILED | Reconciliation failed because of a non-recoverable error |

### Database Relationship

The current design uses two independent tables:

- `products`
- `reconciliation_audit_logs`

Audit entries are not dependent on individual product records. This allows reconciliation attempts and failures to be recorded even when a submitted SKU does not exist.

---

## 6. Environment Configuration

The application reads configuration from environment variables and `.env`.

Create a `.env` file in the project root:

```dotenv
API_KEY_SECRET=your-long-random-secret
```

**Important security practices:**

- Never commit `.env` to Git.
- Never expose the API key in screenshots or logs.
- Use a strong random secret.
- Use `.env.example` as a configuration template.

### Example Configuration Template

```dotenv
API_KEY_SECRET=replace-with-a-long-random-secret
```

### Database Configuration

Native execution uses:

```text
sqlite+aiosqlite:///./enterprise_inventory.db
```

Docker execution uses:

```text
sqlite+aiosqlite:////data/enterprise_inventory.db
```

The Docker database path points to the persistent `/data` volume.

---

## 7. Native Installation and Execution

### Prerequisites

- Python 3.13
- pip
- PowerShell or terminal

### Step 1: Navigate to the project

```powershell
cd C:\Users\ravik\Downloads\inventory-orchstrator\inventory-orchstrator
```

### Step 2: Create a virtual environment

```powershell
python -m venv .venv
```

A virtual environment isolates project dependencies from the system Python installation.

### Step 3: Activate the environment

```powershell
.venv\Scripts\Activate.ps1
```

### Step 4: Install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

`requirements.txt` includes runtime and testing dependencies.

### Step 5: Configure environment variables

Create `.env` using the configuration described in Section 6.

### Step 6: Initialize the database

The application initializes its database schema during startup.

To insert sample products manually, run:

```powershell
python -m app.seed
```

The seed operation is idempotent: existing product SKUs are not inserted again or overwritten.

### Step 7: Start the API

```powershell
uvicorn app.main:app --reload
```

The application runs at:

```text
http://localhost:8000
```

### Step 8: Verify the health endpoint

```powershell
Invoke-RestMethod http://localhost:8000/health
```

Expected result:

```text
healthy
```

---

## 8. Docker Deployment

Docker provides an isolated environment containing the application and its runtime dependencies.

### Prerequisites

Install:

- Docker Desktop
- Docker Compose

Verify:

```powershell
docker --version
docker compose version
```

### Step 1: Build the Docker image

```powershell
docker compose build
```

The Dockerfile uses a multi-stage build.

**Builder stage:**

- Uses Python 3.13 slim.
- Creates an isolated virtual environment.
- Installs runtime dependencies.

**Runtime stage:**

- Starts from a clean Python 3.13 slim image.
- Copies the installed virtual environment.
- Copies application source code.
- Creates a non-root application user.
- Uses `/data` for SQLite persistence.

### Step 2: Start the application

```powershell
docker compose up -d
```

The Compose startup command executes:

```bash
python -m app.seed
```

before starting Uvicorn.

This automatically:

1. Initializes the database schema.
2. Inserts missing sample products.
3. Preserves existing product data.
4. Starts the API server.

### Step 3: Check container status

```powershell
docker compose ps
```

The expected status is:

```text
Up (healthy)
```

### Step 4: Inspect application logs

```powershell
docker compose logs -f inventory-api
```

### Step 5: Test the health endpoint

```powershell
Invoke-RestMethod http://localhost:8001/health
```

Expected response:

```text
healthy
```

### Step 6: Execute the application inside Docker

```powershell
docker compose exec inventory-api whoami
```

Expected:

```text
app
```

The application runs using a non-root Linux user.

### Step 7: Stop the containers

```powershell
docker compose down
```

This stops and removes the containers and default network.

The named database volume is preserved.

**Important:** Avoid this command unless you intentionally want to delete persistent database data:

```powershell
docker compose down -v
```

The `-v` option removes the Compose-managed volume.

---

## 9. API Documentation

Base URL for the current Docker configuration:

```text
http://localhost:8001
```

All protected endpoints require:

```http
X-Api-Key: your-api-key
```

### 9.1 Health Check

**Endpoint**

```http
GET /health
```

Authentication: Not required.

Example:

```powershell
Invoke-RestMethod http://localhost:8001/health
```

Expected response:

```text
healthy
```

### 9.2 Get Inventory

**Endpoint**

```http
GET /api/v1/inventory
```

Authentication: Required.

Headers:

```http
X-Api-Key: your-api-key
```

Supported query parameters:

| Parameter | Description | Validation |
|---|---|---|
| limit | Maximum number of records | 1–100 |
| offset | Number of records to skip | Must be >= 0 |
| min_stock | Minimum stock quantity | Must be >= 0 |

The endpoint returns active products and supports optional minimum-stock filtering.

**Example:**

```http
GET /api/v1/inventory?limit=10&offset=0
```

PowerShell example:

```powershell
$headers = @{
    "X-Api-Key" = "your-api-key"
}

Invoke-RestMethod `
    -Uri "http://localhost:8001/api/v1/inventory?limit=10&offset=0" `
    -Headers $headers
```

**Example response:**

```json
{
  "items": [
    {
      "sku": "LAPTOP-001",
      "name": "Business Laptop",
      "stock_quantity": 50,
      "warehouse_location": "WH-MUM-01",
      "base_price_usd": 899.99,
      "is_active": true
    }
  ],
  "pagination": {
    "total": 4,
    "limit": 10,
    "offset": 0
  }
}
```

The total count represents the records matching the active-product and filter conditions.

### 9.3 Inventory Reconciliation

**Endpoint**

```http
POST /api/v1/inventory/reconcile
```

Authentication: Required.

The endpoint accepts an inventory manifest.

**Request format:**

```json
{
  "manifest": [
    {
      "sku": "LAPTOP-001",
      "stock_quantity": 60
    },
    {
      "sku": "MOUSE-001",
      "stock_quantity": 100
    }
  ]
}
```

**PowerShell example:**

```powershell
$headers = @{
    "X-Api-Key" = "your-api-key"
}

$body = @{
    manifest = @(
        @{
            sku = "LAPTOP-001"
            stock_quantity = 60
        },
        @{
            sku = "MOUSE-001"
            stock_quantity = 100
        }
    )
} | ConvertTo-Json -Depth 5

Invoke-RestMethod `
    -Uri "http://localhost:8001/api/v1/inventory/reconcile" `
    -Method Post `
    -Headers $headers `
    -ContentType "application/json" `
    -Body $body
```

**Expected response:**

HTTP `202 Accepted`.

The response contains a task identifier:

```json
{
  "task_id": "generated-task-uuid"
}
```

The endpoint accepts the request and schedules background reconciliation. HTTP 202 does not mean the background operation has already completed.

---

## 10. API Authentication

The application implements API key authentication through custom middleware.

### Authentication Workflow

```text
Incoming Request
       |
       v
Read X-Api-Key Header
       |
       v
Compare With API_KEY_SECRET
       |
       +----------------------+
       |                      |
       v                      v
   Valid Key              Invalid Key
       |                      |
       v                      v
 Continue Request         HTTP 401
```

The middleware uses constant-time comparison through Python's `hmac.compare_digest()`.

### Authentication Responses

| Scenario | HTTP status |
|---|---:|
| Valid API key | 200 or endpoint-specific success |
| Missing API key | 401 |
| Invalid API key | 401 |
| Missing configured server secret | 401 |
| Public health endpoint | 200 |

Only `/health` is exempted from the API key middleware in the current implementation.

Consequently, `/docs`, `/redoc`, and `/openapi.json` are protected and return HTTP 401 without authentication.

---

## 11. Inventory Reconciliation Workflow

Reconciliation is the core business operation of this project.

### Step 1: Receive Manifest

The client submits product SKUs and their latest stock quantities.

### Step 2: Validate Manifest

Pydantic validates:

- SKU format and length.
- Stock quantity.
- Manifest size.
- Duplicate SKUs.

Invalid requests are rejected before background processing.

### Step 3: Schedule Background Task

FastAPI BackgroundTasks schedules the reconciliation worker.

The API returns HTTP 202 Accepted.

### Step 4: Match SKUs

The worker searches for existing product records using the submitted SKUs.

### Step 5: Update Stock

When a product exists, its stock quantity is updated.

The submitted quantity becomes the new stock quantity; it is not added to the existing quantity.

### Step 6: Identify Unknown SKUs

Unknown SKUs are not inserted into the product table.

They are included in the reconciliation audit information.

### Step 7: Record Audit

The worker records:

- Reconciliation status.
- Number of matched SKUs processed.
- Timestamp.
- Unknown SKU information or error details.

### Step 8: Commit Transaction

Successful stock updates and their corresponding audit entry are committed together.

This protects the consistency of inventory updates.

---

## 12. Database Transactions and Atomicity

The reconciliation worker uses SQLAlchemy transaction management.

Conceptually:

```python
async with session.begin():

    # Match existing products

    # Update stock quantities

    # Identify unknown SKUs

    # Insert reconciliation audit record

    # Commit transaction automatically
```

If an exception occurs before commit, the transaction is rolled back.

This prevents partial stock updates from being committed without their corresponding success audit record.

Failure auditing is attempted separately when necessary.

---

## 13. SQLite Concurrency and Retry Strategy

SQLite is lightweight and suitable for this project, but it has a concurrency limitation: it allows only one active writer at a time.

When multiple reconciliation requests attempt database writes concurrently, SQLite can report a locked or busy error.

### Implemented Strategy

The application uses:

1. Write-Ahead Logging (WAL).
2. SQLite busy timeout.
3. Database connection timeout.
4. Transaction boundaries.
5. Lock-error detection.
6. Retry handling.
7. Fallback audit recording.

### Retry Workflow

```text
Reconciliation Request
          |
          v
    Start Transaction
          |
          v
     Database Write
          |
          v
      Success?
       /   \
     Yes    No
      |      |
      v      v
    Commit  Check Lock Error
              |
              v
          Retry Count
              |
       +------+------+
       |             |
     < 3 retries   3 attempts
       |             |
       v             v
     Retry       RETRY_FALLBACK
                     |
                     v
               Record Audit
```

The worker makes up to three total attempts for SQLite lock errors.

Non-lock database failures are treated as failures rather than retryable lock conditions.

Fallback audit recording is best effort because the database may remain locked even after the reconciliation attempts are exhausted.

### Why WAL?

Write-Ahead Logging allows readers to continue reading while a writer is active in many situations.

However, WAL does not enable multiple simultaneous SQLite writers.

### Future Scalability

For higher write concurrency, PostgreSQL would be a more suitable database.

For durable background jobs, a dedicated task queue such as Celery or another persistent job-processing system could be introduced.

The current FastAPI BackgroundTasks implementation runs within the application process and is not a durable distributed task queue.

---

## 14. Database Seeding

The application provides:

```text
app/seed.py
```

The seed script creates the database schema and inserts five sample products.

| SKU | Product | Stock | Warehouse | Active |
|---|---|---:|---|---|
| LAPTOP-001 | Business Laptop | 50 | WH-MUM-01 | Yes |
| MOUSE-001 | Wireless Mouse | 150 | WH-MUM-01 | Yes |
| KEYBOARD-001 | Mechanical Keyboard | 75 | WH-HYD-01 | Yes |
| MONITOR-001 | 27-inch Monitor | 30 | WH-HYD-01 | Yes |
| WEBCAM-001 | HD Webcam | 0 | WH-DEL-01 | No |

### Run Seeding Manually

```powershell
python -m app.seed
```

### Idempotency

The seeding operation checks existing product SKUs before inserting new records.

First execution:

```text
inserted=5 existing=0
```

Subsequent execution:

```text
inserted=0 existing=5
```

Existing stock quantities are not overwritten by repeated seeding.

Docker Compose executes this seeding step automatically before starting the application.

---

## 15. Docker Image Security and Optimization

The Dockerfile uses a multi-stage build.

### Builder Stage

- Uses `python:3.13-slim`.
- Creates an isolated virtual environment.
- Installs runtime dependencies.
- Keeps dependency installation separate from the final runtime image.

### Runtime Stage

- Uses a fresh `python:3.13-slim` image.
- Copies the installed virtual environment.
- Copies application source.
- Creates a non-root user called `app`.
- Stores database files in `/data`.
- Exposes port 8000 inside the container.

### Non-Root Execution

The container runs as:

```text
app
```

rather than root.

This follows the principle of least privilege.

### Persistent Storage

Docker Compose defines a named volume:

```yaml
volumes:
  inventory_data:
```

The volume is mounted at:

```text
/data
```

Therefore, the SQLite database survives normal container restarts and container recreation.

### Docker Port Mapping

The current configuration uses:

```yaml
ports:
  - "8001:8000"
```

This means:

- Host machine: port 8001.
- Container: port 8000.

The application can be accessed from:

```text
http://localhost:8001
```

---

## 16. Automated Testing

The project uses pytest, pytest-asyncio, and HTTPX.

### Run All Tests

Activate the virtual environment and execute:

```powershell
python -m pytest -v
```

Using `python -m pytest` ensures pytest runs under the currently active Python interpreter.

### Test Coverage

| Test file | Responsibility |
|---|---|
| `test_middleware.py` | API key authentication |
| `test_inventory.py` | Inventory pagination and filtering |
| `test_reconciliation.py` | Reconciliation, validation, audit, and retry behavior |
| `conftest.py` | Test database and shared fixtures |

### Covered Test Scenarios

**Authentication**

- Missing API key.
- Invalid API key.
- Valid API key.
- Public health endpoint.

**Inventory**

- Pagination.
- Offset handling.
- Minimum-stock filtering.

**Reconciliation**

- Successful stock update.
- Audit record creation.
- Duplicate SKU validation.
- Background task scheduling.
- SQLite lock detection.
- Successful retry after temporary locks.
- Retry exhaustion and fallback audit.

### Verified Test Result

```text
11 passed
```

The test suite completed successfully with no test failures.

In addition to automated tests, the running Docker application was verified through live API requests for:

- Authenticated inventory retrieval.
- Successful reconciliation.
- Stock restoration.
- Unknown SKU handling.
- Mixed known and unknown SKU reconciliation.
- Audit record creation.
- Pagination.
- Minimum-stock filtering.
- Invalid manifest rejection.
- Authentication and query parameter boundaries.

---

## 17. Troubleshooting

### Problem 1: API key returns HTTP 401

Check:

- `.env` exists.
- `API_KEY_SECRET` is configured.
- The request contains the `X-Api-Key` header.
- The key used by the client matches the Docker container configuration.

After changing `.env`, recreate the container:

```powershell
docker compose up -d --force-recreate
```

Do not share the actual secret when troubleshooting.

### Problem 2: Container is unhealthy

Inspect:

```powershell
docker compose ps
docker compose logs --tail 100 inventory-api
```

Check whether:

- Database initialization completed.
- Dependencies installed successfully.
- Uvicorn started.
- The health endpoint responds.

### Problem 3: SQLite database is locked

Inspect application logs:

```powershell
docker compose logs --tail 100 inventory-api
```

The application already configures WAL mode, busy timeout, and retry handling for transient SQLite locks.

Avoid manually deleting database, WAL, or shared-memory files while the application is running.

### Problem 4: Module not found

Activate the project environment:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Run commands from the project root.

### Problem 5: Docker database data appears missing

Check the named volume:

```powershell
docker volume ls
```

Inspect the container:

```powershell
docker compose exec inventory-api ls -lah /data
```

Avoid `docker compose down -v` if you need to preserve the database.

---

## 18. Important Design Decisions

| Design decision | Reason |
|---|---|
| FastAPI | Asynchronous REST API development |
| SQLAlchemy ORM | Structured database operations and transaction support |
| SQLite | Lightweight relational persistence |
| aiosqlite | Async SQLite access |
| API key middleware | Protect application endpoints |
| BackgroundTasks | Execute reconciliation after request acceptance |
| SKU matching | Identify existing inventory products |
| Audit logging | Maintain a reconciliation history |
| Atomic transactions | Protect consistency of stock updates and audit entries |
| WAL mode | Improve SQLite reader/writer concurrency |
| Retry mechanism | Handle transient database lock errors |
| Multi-stage Docker build | Separate dependency installation from runtime |
| Non-root container user | Reduce container privileges |
| Docker named volume | Persist database data |
| Idempotent seed operation | Prevent duplicate sample records |

---

## 19. Known Limitations and Future Improvements

The following are potential future enhancements, not requirements of the current implementation.

1. **Database scalability:** Migrate from SQLite to PostgreSQL if concurrent write workloads increase.
2. **Durable background processing:** Introduce Celery, Redis, or another persistent job queue if tasks must survive application restarts.
3. **Task tracking:** Add a reconciliation task status API to query task progress and completion.
4. **Authentication improvements:** Introduce scoped API keys or OAuth2/JWT authentication if multiple clients require different permissions.
5. **Monitoring:** Integrate structured metrics, tracing, and centralized logging.
6. **Database backup:** Implement scheduled database backups and recovery procedures.
7. **Rate limiting:** Protect public-facing deployments from excessive requests.
8. **Deployment security:** Use managed secrets and HTTPS in a production environment.

---

## 20. Final Project Summary

The Enterprise Inventory Orchestrator demonstrates how to build an asynchronous backend service that manages inventory updates and reconciliation operations.

The project brings together:

- REST API development.
- API key authentication.
- Request validation.
- SQLAlchemy ORM.
- Asynchronous SQLite access.
- Background processing.
- Transaction management.
- Audit logging.
- Database concurrency handling.
- Docker containerization.
- Persistent storage.
- Automated testing.

The implementation has been tested through an automated test suite and live Docker API integration checks.

**The result is a containerized inventory management service with secure API access, background reconciliation, transactional stock updates, audit history, and SQLite lock-recovery handling.**