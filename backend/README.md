# Network Control Plane — Backend Service

The **Network Control Plane Backend** is an asynchronous, provider-neutral control plane service engineered for containerized and virtualized workload networking. It coordinates network discovery, topology modeling, IP address management (IPAM), declarative policy enforcement, drift detection, and agent orchestration across diverse infrastructure runtimes.

---

## 1. Architecture & Technology Stack

The backend architecture is strictly decoupled from underlying infrastructure providers, operating on vendor-agnostic domain models and standardized adapter capability contracts.

| Layer | Component | Approved Technology |
|---|---|---|
| **API Framework** | Web Service & Routing | [FastAPI](https://fastapi.tiangolo.com/), [Starlette](https://www.starlette.io/), [Pydantic v2](https://docs.pydantic.dev/latest/) |
| **Persistence** | Asynchronous ORM | [SQLAlchemy 2.0 (Async)](https://docs.sqlalchemy.org/en/20/), [asyncpg](https://magicstack.github.io/asyncpg/) |
| **Database** | Relational Store | PostgreSQL 16 |
| **Database Migrations** | Schema Versioning | [Alembic](https://alembic.sqlalchemy.org/en/latest/) |
| **Cache & Task Queue** | Asynchronous Worker Broker | Redis 7, [ARQ](https://arq-docs.helpmanual.io/) |
| **Observability** | Telemetry & Health | [Prometheus FastAPI Instrumentator](https://github.com/trallnag/prometheus-fastapi-instrumentator) (`/metrics`), `/health` |
| **Package Management** | Environment & Dependency Management | [`uv`](https://github.com/astral-sh/uv), [Hatchling](https://hatch.pypa.io/latest/) |
| **Test Suite** | Testing & In-Memory Test DB | [Pytest](https://docs.pytest.org/), [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio), [aiosqlite](https://aiosqlite.omnilib.dev/) |
| **Code Hygiene** | Linter, Formatter & Type Checker | [Ruff](https://docs.astral.sh/ruff/), [Mypy](https://mypy-lang.org/) |

---

## 2. Directory Layout

```text
backend/
├── app/
│   ├── api/                    # API route definitions
│   │   ├── router.py           # Main APIRouter (/api/v1 aggregation)
│   │   └── v1/                 # Resource routes (hosts, networks, containers, etc.)
│   ├── core/                   # Application configuration, DB engine, security, logging
│   │   ├── config.py           # Pydantic Settings and environment variable loader
│   │   ├── database.py         # SQLAlchemy async engine, session factory, Base
│   │   └── security.py         # JWT tokens, password hashing, RBAC claims
│   ├── models/                 # SQLAlchemy ORM declarative models
│   ├── schemas/                # Pydantic v2 validation and serialization schemas
│   ├── services/               # Core business logic (IPAM, audit, jobs, host orchestration)
│   ├── providers/              # Provider adapters (Docker, Podman Netavark, Hyper-V, Bridge)
│   └── main.py                 # FastAPI application factory, lifespan, CORS, and Prometheus
├── migrations/                 # Alembic migration scripts and env.py
├── tests/                      # Pytest test suite
│   ├── unit/                   # Isolated unit tests (schemas, models, algorithms)
│   └── integration/            # API endpoint integration tests (SQLite in-memory async)
├── alembic.ini                 # Alembic configuration
├── Dockerfile                  # Container build definition for backend service
├── pyproject.toml              # Project dependencies, packaging, and tool configs
└── README.md                   # This developer onboarding guide
```

---

## 3. Mandatory Architectural Invariants

All contributions must strictly uphold the architectural invariants defined in `AGENTS.md`:

* **Invariant A1 — Provider Neutrality:** Core domain models (`app/models/`, `app/schemas/`, `app/services/`) MUST NOT import provider SDKs (such as `docker-py` or Kubernetes client libraries). Provider SDKs belong strictly inside provider adapter packages (`app/providers/` or `app/docker/`).
* **Invariant A2 — Adapter Isolation:** Infrastructure runtimes interact with the control plane strictly through capability contracts (`discover()`, `inspect()`, `create_network()`, `delete_network()`, `attach_endpoint()`, `detach_endpoint()`, `get_connectivity()`).
* **Invariant A3 — Read Before Write & Safety Verification:** Any mutating network operation must execute a validation and safety risk analysis prior to execution: `Discover -> Validate -> Risk Analysis / Preview -> User Approval -> Execute -> Verify -> Audit Event`.
* **Invariant A4 — API Socket Isolation:** Frontend clients and remote consumers must NEVER communicate directly with Docker sockets or provider APIs. All interactions pass through FastAPI authentication, RBAC, policy checking, and audit recording.

---

## 4. Prerequisites

Before setting up the backend locally, ensure you have the following installed:

1. **Python 3.12+** (tested against Python 3.12.x).
2. **`uv` Package Manager** (recommended for ultra-fast dependency resolution and virtual environment management):
   ```bash
   # Install uv via curl (Linux/macOS)
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Install uv via PowerShell (Windows)
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```
3. **Docker & Docker Compose** (for running local PostgreSQL and Redis instances).

---

## 5. Local Development Setup

### 5.1 Clone & Navigate
```bash
git clone https://github.com/ServerAutomation-IN/Network-Control-Plane.git
cd Network-Control-Plane/backend
```

### 5.2 Virtual Environment & Dependencies
Create an isolated virtual environment and install backend dependencies in editable mode:

```bash
# Create virtual environment
uv venv .venv

# Activate virtual environment
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Windows (cmd):
.venv\Scripts\activate.bat
# Linux / macOS:
source .venv/bin/activate

# Install package in editable mode with development dependencies
uv pip install -e ".[dev]"
```

### 5.3 Configure Environment Variables
Copy the template configuration from `deployment/.env.example` into `backend/.env`:

```bash
# From workspace root:
cp deployment/.env.example backend/.env
```

Key environment variables in `backend/.env`:
* `SECRET_KEY`: Cryptographically secure secret for JWT tokens and cryptographic operations.
* `POSTGRES_SERVER`, `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`: PostgreSQL connection settings.
* `REDIS_HOST`, `REDIS_PORT`: Redis cache and background queue connection settings.
* `AGENT_API_TOKEN`: Shared bearer token for authenticating host agent heartbeats (optional for local testing).

---

## 6. Running Local Infrastructure

To spin up local PostgreSQL and Redis backing services:

```bash
# From repository root
docker compose up -d postgres redis
```

---

## 7. Database Migrations with Alembic

The database schema is managed via Alembic migrations.

```bash
# Apply all pending migrations to the database
uv run alembic upgrade head

# Generate a new migration script after modifying models in app/models/
uv run alembic revision --autogenerate -m "describe_change_here"

# Rollback the last migration
uv run alembic downgrade -1
```

> **Note:** For local development and test runs using SQLite in-memory databases, the FastAPI application lifecycle context automatically invokes `Base.metadata.create_all` on startup.

---

## 8. Running the Development Server

Start the FastAPI application with live hot-reloading:

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Available Endpoints & Documentation
* **Interactive OpenAPI Docs (Swagger UI):** [`http://localhost:8000/docs`](http://localhost:8000/docs)
* **Alternative API Docs (ReDoc):** [`http://localhost:8000/redoc`](http://localhost:8000/redoc)
* **System Health Check:** [`http://localhost:8000/health`](http://localhost:8000/health)
* **Prometheus Telemetry Metrics:** [`http://localhost:8000/metrics`](http://localhost:8000/metrics)
* **Host Agent Installers:**
  - Linux/POSIX installer: `http://localhost:8000/install.sh`
  - Windows PowerShell installer: `http://localhost:8000/install.ps1`
* **Cloud Event Ingestion Webhooks:**
  - Ingestion gateway: `http://localhost:8000/api/v1/webhooks/cloud/{provider}` (AWS, Azure, GCP, VMware)

---

## 9. Testing & Test Suites

The backend test suite uses `pytest` with `pytest-asyncio` and an in-memory `aiosqlite` database engine to provide fast, isolated, and deterministic test execution without requiring an active PostgreSQL instance.

```bash
# Run the entire test suite
uv run pytest -v

# Run only unit tests
uv run pytest tests/unit/ -v

# Run only integration tests
uv run pytest tests/integration/ -v

# Run a specific test module
uv run pytest tests/integration/test_agent_bootstrap_wizard.py -v

# Run tests with test coverage reporting
uv run pytest --cov=app tests/
```

---

## 10. Linting, Formatting & Type Checking

To ensure code hygiene and enforce repository standards:

```bash
# Check code style with Ruff
uv run ruff check app/

# Automatically fix linting violations where supported
uv run ruff check --fix app/

# Verify formatting with Ruff
uv run ruff format --check app/

# Run static type checking with Mypy
uv run mypy app/
```

---

## 11. Packaging & Container Builds

The backend is packaged using Hatchling compliant with PEP 621 (`pyproject.toml`):

```bash
# Validate packaging build locally
uv build --wheel

# Build production container image
docker build -t network-control-plane-backend:latest -f Dockerfile .
```
