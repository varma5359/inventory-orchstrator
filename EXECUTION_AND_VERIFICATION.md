# Enterprise Inventory Orchestrator
# Execution and Verification Guide

This document explains how to:

1. Set up and execute the application.
2. Run it locally using Python.
3. Run it using Docker.
4. Verify API authentication.
5. Test inventory retrieval, pagination, and filtering.
6. Perform inventory reconciliation.
7. Verify stock updates and unknown SKU handling.
8. Verify audit logs directly in SQLite.
9. Execute automated tests.
10. Verify Docker persistence and application security.
11. Determine whether the assignment is complete.

All commands in this document are written for **Windows PowerShell**.

---

# 1. Project Overview

The Enterprise Inventory Orchestrator is an asynchronous inventory management application built using:

- Python 3.13
- FastAPI
- SQLAlchemy
- SQLite
- aiosqlite
- Pydantic
- Uvicorn
- pytest
- Docker
- Docker Compose

The primary objective is to receive inventory manifests, match incoming product SKUs against existing database records, update stock quantities, and maintain an audit trail.

## Expected application workflow

```text
External Inventory System
          |
          v
     FastAPI API
          |
          v
   API Key Middleware
          |
          v
   Request Validation
          |
          v
  Reconciliation Endpoint
          |
          v
   HTTP 202 Accepted
          |
          v
   Background Worker
          |
          v
      SKU Matching
          |
     +----+-----+
     |          |
     v          v
 Known SKU   Unknown SKU
     |          |
     v          v
 Update Stock  Record in Audit
     |          |
     +-----+----+
           |
           v
    Database Transaction
           |
           v
      SQLite Database
```

---

# 2. Open the Project

Open PowerShell.

Navigate to the project directory:

```powershell
cd "C:\Users\ravik\Downloads\inventory-orchstrator\inventory-orchstrator"
```

Verify the current directory:

```powershell
Get-Location
```

Check the project structure:

```powershell
Get-ChildItem
```

You should find files and directories similar to:

```text
app/
tests/
.env
.env.example
.dockerignore
Dockerfile
docker-compose.yml
requirements.txt
requirements-runtime.txt
pytest.ini
README.md
```

The application source code is inside `app/`, while automated tests are inside `tests/`.

---

# 3. Configure the Environment

The application requires an API key secret.

Open `.env`:

```powershell
notepad .env
```

Ensure it contains:

```dotenv
API_KEY_SECRET=your-long-random-secret
```

Use your actual configured secret instead of the example value.

**Security precautions:**

- Never commit `.env` to a public repository.
- Never paste your real API key into screenshots.
- Never print your secret when demonstrating the project.
- Use `.env.example` only as a template.

The application reads the configuration using Pydantic Settings.

---

# 4. Execution Method A — Run Locally

This method runs the application directly through Python.

## Step 4.1 — Create a virtual environment

```powershell
python -m venv .venv
```

A virtual environment isolates project dependencies.

## Step 4.2 — Activate the virtual environment

```powershell
.venv\Scripts\Activate.ps1
```

Your terminal should display:

```text
(.venv)
```

## Step 4.3 — Install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The requirements include the runtime packages and testing tools.

## Step 4.4 — Verify dependencies

```powershell
python -m pip check
```

Expected:

```text
No broken requirements found.
```

## Step 4.5 — Initialize and seed the database

```powershell
python -m app.seed
```

The seed script creates the database schema and inserts missing sample products.

The seed operation is idempotent, meaning that running it again does not insert duplicate product records or overwrite existing stock quantities.

## Step 4.6 — Start FastAPI

```powershell
uvicorn app.main:app --reload
```

Expected application address:

```text
http://localhost:8000
```

Keep this terminal open while testing the application.

Open a second PowerShell terminal for the API verification steps.

---

# 5. Execution Method B — Run with Docker

Docker is the recommended demonstration method because it verifies the containerized application and persistent database configuration.

Open another PowerShell terminal.

Navigate to the project root:

```powershell
cd "C:\Users\ravik\Downloads\inventory-orchstrator\inventory-orchstrator"
```

## Step 5.1 — Verify Docker

```powershell
docker --version
docker compose version
```

Both commands should display installed versions.

## Step 5.2 — Validate Docker Compose configuration

```powershell
docker compose config --quiet
```

Expected:

```text
No configuration errors.
```

The command should complete without an error.

## Step 5.3 — Build the Docker image

```powershell
docker compose build
```

This builds the application using the multi-stage Dockerfile.

The builder stage installs dependencies. The runtime stage receives the installed environment and application source.

## Step 5.4 — Start the application

```powershell
docker compose up -d
```

Docker Compose:

1. Creates the application container.
2. Creates or reuses the persistent database volume.
3. Executes the database seed command.
4. Starts Uvicorn.

## Step 5.5 — Verify container status

```powershell
docker compose ps
```

Expected:

- Container is running.
- Health status becomes `healthy`.

## Step 5.6 — Check application logs

```powershell
docker compose logs --tail 50 inventory-api
```

Look for successful startup messages.

## Step 5.7 — Verify health

```powershell
Invoke-RestMethod -Uri "http://localhost:8001/health"
```

Expected:

```text
healthy
```

The Docker application is accessible through:

```text
http://localhost:8001
```

**Important:** The current Compose configuration maps host port 8001 to container port 8000.

---

# 6. Prepare API Authentication

The protected endpoints require an API key.

For Docker execution, use the same secret configured in `.env`.

In your PowerShell terminal:

```powershell
$apiKey = Read-Host "Enter your API key"
```

Create the headers:

```powershell
$headers = @{
    "X-Api-Key" = $apiKey
}
```

This avoids printing the secret in your commands.

For the following examples, the Docker base URL is:

```powershell
$baseUrl = "http://localhost:8001"
```

For native execution, use:

```powershell
$baseUrl = "http://localhost:8000"
```

---

# 7. Verification 1 — Health Endpoint

Execute:

```powershell
Invoke-RestMethod -Uri "$baseUrl/health"
```

Expected:

```text
healthy
```

What does this prove?

- The application server is responding.
- The health endpoint is accessible.
- The application can receive HTTP requests.

Note: This is an application health check, not a complete database integrity check.

---

# 8. Verification 2 — API Key Authentication

Authentication is implemented using custom middleware.

## Test A — Request without API key

```powershell
$response = Invoke-WebRequest `
    -Uri "$baseUrl/api/v1/inventory" `
    -SkipHttpErrorCheck

$response.StatusCode
```

Expected:

```text
401
```

## Test B — Request with invalid API key

```powershell
$invalidHeaders = @{
    "X-Api-Key" = "invalid-key"
}

$response = Invoke-WebRequest `
    -Uri "$baseUrl/api/v1/inventory" `
    -Headers $invalidHeaders `
    -SkipHttpErrorCheck

$response.StatusCode
```

Expected:

```text
401
```

## Test C — Request with valid API key

```powershell
$inventory = Invoke-RestMethod `
    -Uri "$baseUrl/api/v1/inventory" `
    -Headers $headers

$inventory
```

Expected:

```text
Successful inventory response
```

### What does this prove?

- Missing credentials are rejected.
- Invalid credentials are rejected.
- Valid credentials are accepted.
- The middleware protects the inventory endpoint.

The `/health` endpoint is intentionally public.

The current implementation also protects `/docs` and `/openapi.json`.

---

# 9. Verification 3 — Initial Inventory

Retrieve all active inventory records:

```powershell
$inventory = Invoke-RestMethod `
    -Uri "$baseUrl/api/v1/inventory" `
    -Headers $headers

$inventory.items |
    Format-Table sku, name, stock_quantity, warehouse_location
```

The initial sample inventory contains:

| SKU | Product | Stock |
|---|---|---:|
| KEYBOARD-001 | Mechanical Keyboard | 75 |
| LAPTOP-001 | Business Laptop | 50 |
| MONITOR-001 | 27-inch Monitor | 30 |
| MOUSE-001 | Wireless Mouse | 150 |

The inactive webcam is not returned by the active-only inventory endpoint.

### What does this prove?

- Product records are available.
- Database retrieval works.
- The active-product filter works.

---

# 10. Verification 4 — Pagination

The inventory API supports:

- `limit`
- `offset`

## Page 1

```powershell
$page1 = Invoke-RestMethod `
    -Uri "$baseUrl/api/v1/inventory?limit=2&offset=0" `
    -Headers $headers

$page1.items |
    Format-Table sku, stock_quantity

$page1.pagination
```

## Page 2

```powershell
$page2 = Invoke-RestMethod `
    -Uri "$baseUrl/api/v1/inventory?limit=2&offset=2" `
    -Headers $headers

$page2.items |
    Format-Table sku, stock_quantity

$page2.pagination
```

### Expected behavior

- Page 1 returns the first two matching records.
- Page 2 returns the next two matching records.
- The pages should contain different SKUs.
- Pagination metadata should report the total, limit, and offset.

### What does this prove?

The application supports database pagination rather than simply returning every record.

---

# 11. Verification 5 — Minimum Stock Filter

Execute:

```powershell
$filtered = Invoke-RestMethod `
    -Uri "$baseUrl/api/v1/inventory?min_stock=100" `
    -Headers $headers

$filtered.items |
    Format-Table sku, stock_quantity
```

Expected:

```text
MOUSE-001    150
```

Only active products with stock quantities greater than or equal to 100 should be returned.

### What does this prove?

The application supports conditional inventory filtering.

---

# 12. Verification 6 — Successful Inventory Reconciliation

This is the most important business-functionality demonstration.

First, check the original laptop stock:

```powershell
$before = Invoke-RestMethod `
    -Uri "$baseUrl/api/v1/inventory" `
    -Headers $headers

$before.items |
    Where-Object sku -eq "LAPTOP-001" |
    Format-Table sku, stock_quantity
```

Expected original stock:

```text
LAPTOP-001    50
```

## Step 12.1 — Create a manifest

```powershell
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
```

## Step 12.2 — Submit the manifest

```powershell
$response = Invoke-RestMethod `
    -Uri "$baseUrl/api/v1/inventory/reconcile" `
    -Method Post `
    -Headers $headers `
    -ContentType "application/json" `
    -Body $body

$response
```

Expected response:

```json
{
  "task_id": "generated-task-uuid"
}
```

The HTTP status is:

```text
202 Accepted
```

## Step 12.3 — Verify the updated stock

The API accepts the request before the background worker completes.

Poll the inventory endpoint until the new value appears:

```powershell
$updated = $false

for ($i = 1; $i -le 20; $i++) {

    $current = Invoke-RestMethod `
        -Uri "$baseUrl/api/v1/inventory" `
        -Headers $headers

    $laptop = $current.items |
        Where-Object sku -eq "LAPTOP-001"

    if ($laptop -and $laptop.stock_quantity -eq 60) {
        $updated = $true
        break
    }

    Start-Sleep -Seconds 1
}

if (-not $updated) {
    throw "Laptop stock was not updated within the verification period."
}

Write-Host "PASS: Laptop stock updated successfully."
```

Verify both products:

```powershell
$current.items |
    Where-Object sku -in @("LAPTOP-001", "MOUSE-001") |
    Format-Table sku, stock_quantity
```

Expected:

| SKU | Updated stock |
|---|---:|
| LAPTOP-001 | 60 |
| MOUSE-001 | 100 |

### What does this prove?

- The reconciliation endpoint accepts manifests.
- The API responds with HTTP 202.
- Background processing executes.
- Existing SKUs are matched.
- Stock quantities are updated.

**Important:** HTTP 202 means the task was accepted, not that it has already completed.

---

# 13. Verification 7 — Unknown SKU Handling

The system should not automatically insert unknown products.

Create a manifest containing an unknown SKU:

```powershell
$unknownBody = @{
    manifest = @(
        @{
            sku = "UNKNOWN-DEMO-999"
            stock_quantity = 25
        }
    )
} | ConvertTo-Json -Depth 5
```

Submit:

```powershell
$unknownResponse = Invoke-RestMethod `
    -Uri "$baseUrl/api/v1/inventory/reconcile" `
    -Method Post `
    -Headers $headers `
    -ContentType "application/json" `
    -Body $unknownBody

$unknownResponse
```

Wait briefly:

```powershell
Start-Sleep -Seconds 2
```

Check the inventory:

```powershell
$current = Invoke-RestMethod `
    -Uri "$baseUrl/api/v1/inventory" `
    -Headers $headers

$unknownProduct = $current.items |
    Where-Object sku -eq "UNKNOWN-DEMO-999"

if ($unknownProduct) {
    throw "Unknown SKU was incorrectly inserted."
}

Write-Host "PASS: Unknown SKU was not inserted."
```

### What does this prove?

- Existing products are updated through SKU matching.
- Unknown products are not automatically created.
- Unknown SKU information is retained in the audit record.

---

# 14. Verification 8 — Direct Audit Database Inspection

The audit table is important because it proves that reconciliation results are persisted.

For Docker execution, execute:

```powershell
@'
import sqlite3

db = sqlite3.connect("/data/enterprise_inventory.db")
db.row_factory = sqlite3.Row

rows = db.execute("""
    SELECT
        id,
        timestamp,
        status,
        skus_processed,
        error_message
    FROM reconciliation_audit_logs
    ORDER BY id DESC
""").fetchall()

for row in rows:
    print(dict(row))

db.close()
'@ | docker compose exec -T inventory-api python -
```

You should see records containing:

```text
status: SUCCESS
skus_processed: ...
error_message: ...
```

For the unknown SKU reconciliation, look for:

```text
Unknown SKUs: UNKNOWN-DEMO-999
```

### What does this prove?

- Audit records are written to SQLite.
- Successful reconciliation is recorded.
- Unknown SKU details are retained.
- Audit information survives beyond the original HTTP request.

---

# 15. Verification 9 — Input Validation

The application validates inventory manifests before scheduling reconciliation.

## Test A — Negative stock

```powershell
$invalidBody = @{
    manifest = @(
        @{
            sku = "LAPTOP-001"
            stock_quantity = -10
        }
    )
} | ConvertTo-Json -Depth 5

$response = Invoke-WebRequest `
    -Uri "$baseUrl/api/v1/inventory/reconcile" `
    -Method Post `
    -Headers $headers `
    -ContentType "application/json" `
    -Body $invalidBody `
    -SkipHttpErrorCheck

$response.StatusCode
```

Expected:

```text
422
```

## Test B — Duplicate SKUs

```powershell
$duplicateBody = @{
    manifest = @(
        @{
            sku = "LAPTOP-001"
            stock_quantity = 60
        },
        @{
            sku = "LAPTOP-001"
            stock_quantity = 70
        }
    )
} | ConvertTo-Json -Depth 5

$response = Invoke-WebRequest `
    -Uri "$baseUrl/api/v1/inventory/reconcile" `
    -Method Post `
    -Headers $headers `
    -ContentType "application/json" `
    -Body $duplicateBody `
    -SkipHttpErrorCheck

$response.StatusCode
```

Expected:

```text
422
```

### What does this prove?

- Negative stock quantities are rejected.
- Duplicate SKUs are rejected.
- Invalid requests do not reach the background worker.
- Invalid manifests do not change inventory records.

---

# 16. Verification 10 — Automated Tests

Open PowerShell in the project root.

Activate the virtual environment:

```powershell
.venv\Scripts\Activate.ps1
```

Run all tests:

```powershell
python -m pytest -v
```

Expected result from the verified test run:

```text
11 passed
```

### Test coverage

| Test area | Verification |
|---|---|
| API middleware | Missing, invalid, and valid API keys |
| Inventory API | Pagination and filtering |
| Reconciliation | Stock update and audit creation |
| Manifest validation | Duplicate SKU rejection |
| Background processing | Reconciliation task scheduling |
| Lock detection | SQLite lock error classification |
| Retry mechanism | Recovery after temporary lock |
| Fallback behavior | Retry exhaustion handling |

### Why automated tests matter

Manual testing proves that selected examples work.

Automated testing provides repeatable verification of the application's expected behavior.

The project has both automated tests and live API verification.

---

# 17. Verification 11 — SQLite Retry Handling

SQLite permits only one active writer at a time.

When concurrent write operations occur, SQLite can return a locked or busy error.

The application handles this through:

- WAL mode.
- Busy timeout.
- Connection timeout.
- Transaction management.
- Lock-error detection.
- Three total reconciliation attempts.
- Fallback audit recording.

The retry logic is covered by automated tests.

Run the specific retry tests:

```powershell
python -m pytest -v tests/test_reconciliation.py
```

Look for tests covering:

```text
test_sqlite_lock_error_detection
test_reconciliation_succeeds_after_temporary_locks
test_reconciliation_records_fallback_after_three_locks
```

### What does this prove?

- SQLite lock errors are identified.
- Temporary locks can be retried.
- Retry exhaustion is handled.
- Fallback audit recording is attempted.

These are controlled test scenarios, not a guarantee that every possible production concurrency condition can be recovered.

---

# 18. Verification 12 — Docker Non-Root Execution

Execute:

```powershell
docker compose exec inventory-api whoami
```

Expected:

```text
app
```

### What does this prove?

The application does not run as the root user inside the container.

This follows the principle of least privilege.

---

# 19. Verification 13 — Docker Database Persistence

The Docker Compose configuration uses a named volume for the SQLite database.

To verify persistence, restart the container:

```powershell
docker compose restart inventory-api
```

Wait until the application responds:

```powershell
$healthy = $false

for ($i = 1; $i -le 30; $i++) {

    try {
        $result = Invoke-RestMethod `
            -Uri "$baseUrl/health" `
            -TimeoutSec 3

        if ($result) {
            $healthy = $true
            break
        }
    }
    catch {
        Start-Sleep -Seconds 2
    }
}

if (-not $healthy) {
    throw "Application did not become healthy."
}

Write-Host "PASS: Application is healthy after restart."
```

Inspect the database:

```powershell
@'
import sqlite3

db = sqlite3.connect("/data/enterprise_inventory.db")

products = db.execute(
    "SELECT COUNT(*) FROM products"
).fetchone()[0]

audits = db.execute(
    "SELECT COUNT(*) FROM reconciliation_audit_logs"
).fetchone()[0]

laptop = db.execute("""
    SELECT stock_quantity
    FROM products
    WHERE sku = 'LAPTOP-001'
""").fetchone()

print("Product count:", products)
print("Audit count:", audits)
print("Laptop stock:", laptop[0] if laptop else None)

assert products == 5
assert audits > 0
assert laptop is not None

print("PASS: Database records survived container restart.")

db.close()
'@ | docker compose exec -T inventory-api python -
```

The laptop stock will depend on the reconciliation operations you have performed. The important point is that the value remains stored after restart.

### What does this prove?

- The database is stored in persistent Docker storage.
- Container restart does not delete inventory.
- Audit history remains available.
- The application can restart and access the existing database.

**Important:** Do not execute `docker compose down -v` during this test. That command removes the named volume and its stored database.

---

# 20. Final Technical Verification

Run these commands from the project root.

## Check 1 — Python syntax

```powershell
python -m compileall -q app tests
```

Expected: No syntax errors.

## Check 2 — Dependency consistency

```powershell
python -m pip check
```

Expected:

```text
No broken requirements found.
```

## Check 3 — Automated tests

```powershell
python -m pytest -v
```

Expected:

```text
11 passed
```

## Check 4 — Docker Compose configuration

```powershell
docker compose config --quiet
```

Expected: No configuration errors.

## Check 5 — Docker container status

```powershell
docker compose ps
```

Expected: Application container is running and healthy.

## Check 6 — Container identity

```powershell
docker compose exec inventory-api whoami
```

Expected:

```text
app
```

---

# 21. Final Completion Checklist

Use this checklist before submission.

## Application

- [x] FastAPI application implemented.
- [x] SQLAlchemy Product model implemented.
- [x] ReconciliationAuditLog model implemented.
- [x] Database constraints implemented.
- [x] API key middleware implemented.
- [x] Inventory retrieval endpoint implemented.
- [x] Pagination implemented.
- [x] Minimum-stock filtering implemented.
- [x] Background reconciliation implemented.
- [x] SKU matching implemented.
- [x] Unknown SKU handling implemented.
- [x] Transaction management implemented.
- [x] SQLite lock retry handling implemented.
- [x] Audit logging implemented.

## Validation and Testing

- [x] API authentication tested.
- [x] Pagination tested.
- [x] Inventory filtering tested.
- [x] Reconciliation tested.
- [x] Unknown SKU handling tested.
- [x] Duplicate SKU validation tested.
- [x] Negative stock validation tested.
- [x] Audit records verified.
- [x] Retry logic tested.
- [x] Eleven automated tests passed.

## Docker

- [x] Multi-stage Dockerfile created.
- [x] Docker Compose configured.
- [x] Automatic database initialization implemented.
- [x] Automatic sample data seeding implemented.
- [x] Non-root execution configured.
- [x] Persistent database volume configured.
- [x] Container health check configured.
- [x] Docker API requests verified.

The checkboxes above represent implementation and verification already completed during development. Re-run the commands in this document if you need to produce fresh verification evidence for a new submission.

---

# 22. How to Explain the Project to an Interviewer

If the interviewer asks, "How do you execute your project?", explain:

> I can execute the application in two ways: locally using Python and through Docker.
>
> For local execution, I create a virtual environment, install the requirements, initialize the database, and start the FastAPI server using Uvicorn.
>
> For Docker execution, I build the multi-stage image and start the application using Docker Compose. The startup process initializes the database, inserts sample inventory records, and starts the API.
>
> I verify the application through the health endpoint and then test the protected APIs using the API key.

If the interviewer asks, "How do you know the project is working correctly?", explain:

> I verify the project at three levels.
>
> First, I run automated tests to validate authentication, pagination, reconciliation, audit logging, and retry behavior.
>
> Second, I perform live API integration testing. I submit inventory manifests, verify stock updates, check unknown SKU handling, and inspect the audit records directly in SQLite.
>
> Third, I verify the Docker environment, including container health, non-root execution, and database persistence after a container restart.
>
> This verifies both the application logic and its deployment behavior.

## Important Technical Questions

**1. Does HTTP 202 mean the reconciliation is complete?**

No. It means the request has been accepted for background processing. The current application does not provide a separate task-status endpoint.

**2. Why did you use BackgroundTasks?**

It allows the API to acknowledge the request without waiting for the reconciliation operation to finish. It is suitable for this assignment, but it is not a durable distributed job queue.

**3. Why SQLite?**

SQLite is lightweight and avoids a separate database server. PostgreSQL would be a better choice for a higher-concurrency production workload.

**4. How do you prevent partial database updates?**

I use SQLAlchemy transactions. Stock changes and the success audit record are committed together.

**5. What happens if a SKU is unknown?**

The system does not automatically create a new product. It records the unknown SKU in the audit information.

**6. What happens if SQLite is locked?**

The worker detects transient lock errors and makes up to three total attempts. If all attempts fail, it attempts to record a `RETRY_FALLBACK` audit entry.

**7. What would you improve in the future?**

I would consider PostgreSQL, durable background processing, reconciliation task-status tracking, structured monitoring, and production-grade authentication.

---

# 23. Recommended Interview Demonstration

For a short interview demonstration, follow this order:

| Order | Demonstration | Approximate time |
|---|---|---:|
| 1 | Explain project purpose and architecture | 1 minute |
| 2 | Build and start Docker | 1 minute |
| 3 | Show health endpoint | 30 seconds |
| 4 | Show API authentication | 1 minute |
| 5 | Retrieve inventory and demonstrate pagination | 1 minute |
| 6 | Submit a reconciliation manifest | 2 minutes |
| 7 | Verify stock changes and unknown SKU handling | 1 minute |
| 8 | Show audit logs | 1 minute |
| 9 | Run automated tests | 1 minute |
| 10 | Explain database transactions and SQLite retries | 2 minutes |

**Final recommendation:** Demonstrate the actual business workflow rather than simply showing that the server starts. A successful reconciliation, verified database changes, and an audit record provide much stronger evidence of a working inventory system.

---

# 24. Project Completion Statement

The Enterprise Inventory Orchestrator implements an asynchronous inventory reconciliation service with API key authentication, inventory filtering and pagination, SKU matching, transactional stock updates, unknown SKU tracking, audit logging, SQLite lock retry handling, automated tests, and Docker deployment.

The implementation has been verified using automated tests and live Docker API integration checks.

The project demonstrates practical backend engineering concepts including REST API design, asynchronous execution, ORM-based database operations, transaction management, validation, concurrency handling, containerization, and deployment verification.