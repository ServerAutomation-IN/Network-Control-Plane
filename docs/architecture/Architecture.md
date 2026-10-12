# Network Control Plane — System Architecture Document

**Status:** Active  
**Product Name:** Network Control Plane (Neutral Working Title — *Docknet is NOT the name*)  
**Tagline:** Visualize. Manage. Validate. Govern. Automate Workload Networking.  
**Document Version:** 1.1  
**Blueprint Reference:** `Blueprint.md` (v2.0)  
**Requirements Reference:** `Requirements.md` (v1.0)  
**ADR References:** `ADR-001`, `ADR-002`, `ADR-003`, `ADR-004`  

---

## 1. Architectural Principles & Invariants

The **Network Control Plane** architecture is designed around six foundational invariants:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        ARCHITECTURAL INVARIANTS                        │
├────────────────────────────────────────────────────────────────────────┤
│ A1: Provider Neutrality      │ Core domain must NOT depend on SDKs     │
│ A2: Adapter Isolation        │ Runtimes interact via capability traits │
│ A3: Read Before Write        │ Discover → Validate → Preview → Audit   │
│ A4: API Socket Isolation     │ UI never contacts runtime sockets directly│
│ A5: Deterministic First      │ Automation executes via validated tools │
│ A6: Immutable Audit Trail    │ All mutations leave an audit log record│
└────────────────────────────────────────────────────────────────────────┘
```

1. **A1 — Provider Neutrality:** Core domain models (`Network`, `Workload`, `Endpoint`, `Host`, `Subnet`, `Policy`, `Drift`) are strictly provider-agnostic. Provider SDKs (e.g., Docker SDK, Kubernetes client) are isolated within provider adapters.
2. **A2 — Adapter Isolation:** Runtimes implement explicit capability contracts (`discover()`, `inspect()`, `create_network()`, `delete_network()`, `attach_endpoint()`, `detach_endpoint()`, `get_connectivity()`).
3. **A3 — Read Before Write:** Mutating operations require pre-execution validation, risk assessment, human/policy preview, and post-execution verification.
4. **A4 — API Socket Isolation:** The web interface communicates solely with the control plane FastAPI backend. Underlying Docker sockets or cloud APIs are never exposed directly to the browser.
5. **A5 — Deterministic Core Before AI:** System logic, policy checks, IPAM calculations, and operations operate deterministically without reliance on LLMs. AI operates as a reasoning and recommendation layer.
6. **A6 — Immutable Audit Logging:** Every mutating request creates an asynchronous `Job` and an append-only `AuditEvent`.

---

## 2. High-Level System Architecture

```text
                               ┌────────────────────────────────┐
                               │       Browser / Web UI         │
                               │(React, TS, TanStack Query, Flow│
                               │     ELK.js / Dagre Layouts)    │
                               └───────────────┬────────────────┘
                                               │ HTTP / REST / SSE / WS
                                               ▼
┌───────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 CONTROL PLANE BACKEND (FastAPI)                               │
├──────────────────────────────────────────────┬────────────────────────────────────────────────┤
│  REST API Router, Auth & /metrics            │ Realtime Event Hub (SSE / WebSockets)          │
├──────────────────────────────────────────────┴────────────────────────────────────────────────┤
│                                   CORE DOMAIN & BUSINESS ENGINES                              │
│ ┌──────────────────────┐ ┌──────────────────────┐ ┌──────────────────────┐ ┌────────────────┐ │
│ │  Inventory Service   │ │   Topology Engine    │ │     IPAM Engine      │ │ Policy Engine  │ │
│ └──────────────────────┘ └──────────────────────┘ └──────────────────────┘ └────────────────┘ │
│ ┌──────────────────────┐ ┌──────────────────────┐ ┌──────────────────────┐ ┌────────────────┐ │
│ │     Drift Engine     │ │  ARQ Async Job Queue │ │     Audit Engine     │ │ AI Layer (LLM) │ │
│ └──────────────────────┘ └──────────────────────┘ └──────────────────────┘ └────────────────┘ │
├───────────────────────────────────────────────────────────────────────────────────────────────┤
│                                  PROVIDER ADAPTER CONTRACT LAYER                              │
│ ┌───────────────────────────────────────────────────────────────────────────────────────────┐ │
│ │  Capability Traits: discover() | inspect() | create() | delete() | attach() | detach()     │ │
│ └─────────────────────────────────────────────┬─────────────────────────────────────────────┘ │
└───────────────────────────────────────────────┼───────────────────────────────────────────────┘
                                                │
                       ┌────────────────────────┴────────────────────────┐
                       │                                                 │
                       ▼                                                 ▼
        ┌─────────────────────────────┐                   ┌─────────────────────────────┐
        │       Docker Adapter        │                   │     Kubernetes Adapter      │
        │    (Docker Engine API)      │                   │     (K8s API / Client)      │
        └──────────────┬──────────────┘                   └──────────────┬──────────────┘
                       │                                                 │
                       ▼                                                 ▼
          [ Local / Remote Docker ]                         [ Kubernetes Cluster ]
```

---

## 3. Layered Component Decomposition

### 3.1 Presentation Layer (`frontend/`)
- **Framework:** React 18+, TypeScript, Next.js / Vite.
- **Server-State Management:** **TanStack React Query (`@tanstack/react-query`)** for background query caching, deduplication, and automatic SSE event cache invalidation.
- **Client UI State:** **Zustand** for local component state, **React Hook Form** + **Zod** for form schema validation.
- **Topology Rendering:** **React Flow** backed by dual layout engines: **ELK.js** (for complex layered graphs) and **Dagre** (for fast directed dependency layouts).
- **Real-Time Updates:** WebSockets / Server-Sent Events (SSE) listener.

### 3.2 Control & API Layer (`backend/app/api/`)
- **Framework:** FastAPI (Python 3.12+ async ASGI), Pydantic v2 schemas.
- **Security & RBAC:** JWT / OAuth2 authentication, role-based access control middleware.
- **Async Execution:** **ARQ** (Async Redis Queue) worker process for background job retries and concurrency control.
- **Observability:** **Prometheus FastAPI Instrumentator** exposing standard `/metrics` endpoint for latency and job execution tracking.
- **API Documentation:** Auto-generated OpenAPI v3 schema.

### 3.3 Core Domain Engines (`backend/app/services/`)
- **Inventory Service:** Normalizes host, network, container, and subnet inventory state into unified database entities.
- **Topology Engine:** Calculates network dependency graphs, container isolation paths, and node-edge connectivity maps.
- **IPAM Engine:** CIDR calculation, subnet overlap detection, IP allocation tracking, and gateway conflict validation.
- **Policy Engine:** Evaluates declarative rules (naming conventions, driver restrictions, CIDR boundaries, label rules).
- **Drift Engine:** Compares desired-state YAML specs against actual runtime state to compute diffs and generate remediation plans.
- **Job Engine:** Manages mutation tasks via ARQ queue, tracking state transitions (`PENDING`, `RUNNING`, `SUCCESS`, `FAILED`).

### 3.4 Provider Adapter Layer (`backend/app/docker/` & `agent/`)
- **Standard Interface:** All adapters implement `BaseProviderAdapter`.
- **Docker Adapter (First Implementation):** Uses `docker-py` / HTTP socket client to query Docker Engine, parse network drivers (`bridge`, `overlay`, `macvlan`), and listen to Docker events.
- **Host Agent Protocol:** For remote multi-host setups, a lightweight agent (`network-control-plane-agent`) runs on provider hosts and reports over gRPC/mTLS or HTTPS.

### 3.5 Persistence & Database Layer (`backend/app/core/database.py`)
- **Relational Database:** PostgreSQL 16 managed via **SQLAlchemy 2.0 (Async)** and **Alembic** migrations.
- **Host Secret Encryption:** Symmetric **Fernet (`cryptography`)** field encryption for storing remote host TLS certificates and API tokens at rest.
- **Caching & Event Pub/Sub:** Redis 7 for ARQ task queues, event streaming, and transient state caching.

---

## 4. Normalized Data Model & Entities

```text
  ┌───────────────────┐               ┌───────────────────┐
  │ InfrastructureHost│ 1           * │      Network      │
  ├───────────────────┤───────────────┼───────────────────┤
  │ id (PK)           │               │ id (PK)           │
  │ name, endpoint    │               │ host_id (FK)      │
  │ encrypted_tls_cert│               │ provider_ref_id   │
  │ status, os, arch  │               │ name, driver      │
  └───────────────────┘               └─────────┬─────────┘
                                                │ 1
                                                │
                                                │ *
                                      ┌─────────┴─────────┐
                                      │   NetworkSubnet   │
                                      ├───────────────────┤
                                      │ id (PK)           │
                                      │ network_id (FK)   │
                                      │ subnet (CIDR)     │
                                      │ gateway, ip_range │
                                      └───────────────────┘

  ┌───────────────────┐               ┌───────────────────┐
  │     Container     │ 1           * │ ContainerNetwork  │
  ├───────────────────┤───────────────┼───────────────────┤
  │ id (PK)           │               │ id (PK)           │
  │ host_id (FK)      │               │ container_id (FK) │
  │ provider_ref_id   │               │ network_id (FK)   │
  │ name, image       │               │ ip_address, mac   │
  └───────────────────┘               └───────────────────┘
```

---

## 5. Standardized Provider Capability Contract

```python
from typing import Protocol, List
from app.schemas.inventory import (
    InventorySnapshot, NetworkSpec, NetworkResult,
    EndpointSpec, AttachmentResult, ConnectivityGraph
)

class ProviderAdapterContract(Protocol):
    async def discover(self) -> InventorySnapshot:
        """Discover hosts, networks, and attached endpoints."""
        ...

    async def inspect_network(self, network_ref_id: str) -> dict:
        """Inspect low-level provider details for a network."""
        ...

    async def create_network(self, spec: NetworkSpec) -> NetworkResult:
        """Create a network on the provider runtime."""
        ...

    async def delete_network(self, network_ref_id: str) -> bool:
        """Delete a network on the provider runtime."""
        ...

    async def attach_endpoint(self, spec: EndpointSpec) -> AttachmentResult:
        """Attach a workload endpoint to a network."""
        ...

    async def detach_endpoint(self, network_ref_id: str, endpoint_ref_id: str) -> bool:
        """Detach a workload endpoint from a network."""
        ...

    async def get_connectivity(self, source_id: str, target_id: str) -> ConnectivityGraph:
        """Evaluate provider connectivity between two workloads."""
        ...
```

---

## 6. API Interface Design

The REST API exposes provider-neutral control endpoints under `/api/v1`:

```http
# System & Observability
GET    /health                     - System health check
GET    /metrics                    - Prometheus telemetry metrics

# Hosts Management
GET    /api/v1/hosts               - List managed provider hosts
POST   /api/v1/hosts               - Register host (TLS secrets encrypted at rest)
GET    /api/v1/hosts/{id}          - Get host details
POST   /api/v1/hosts/{id}/sync     - Trigger host inventory synchronization

# Network Operations
GET    /api/v1/networks            - List all normalized networks
POST   /api/v1/networks            - Create network (validated & audited)
GET    /api/v1/networks/{id}       - Network details & configuration
DELETE /api/v1/networks/{id}       - Delete network (requires risk check)
POST   /api/v1/networks/{id}/prune - Analyze and prune candidate networks

# Endpoint & Container Attachments
GET    /api/v1/containers          - List containers & workloads
POST   /api/v1/networks/{id}/containers             - Attach container to network
DELETE /api/v1/networks/{id}/containers/{c_id}     - Detach container from network

# Topology & IPAM
GET    /api/v1/topology            - Graph data (nodes & edges for React Flow)
GET    /api/v1/ipam/conflicts      - Detect overlapping subnets or IP collisions
POST   /api/v1/ipam/validate       - Validate proposed CIDR / IP allocation

# Governance, Drift & Jobs
GET    /api/v1/policies            - Policy list & compliance status
POST   /api/v1/drift/compare       - Compare actual vs desired YAML state
GET    /api/v1/jobs                 - Audit background ARQ job executions
GET    /api/v1/audit                - Search immutable audit event log
```

---

## 7. Operational & Security Architecture

### Operational Safety Workflow
```text
  [ User Action ] ──> [ Schema Validation ] ──> [ Risk Analysis ]
                                                        │
  [ Audit Record ] <── [ ARQ Queue ] <── [ User Approval ]
         │                    │
         ▼                    ▼
  [ Verify State ] <── [ Provider Adapter ]
```

1. **Input Schema Validation:** Incoming requests are validated against Pydantic models.
2. **Safety Risk Assessment:** Mutating requests run pre-checks (checking attached containers, Compose dependencies) and assign a Risk Level (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
3. **Execution & Audit:** Actions execute asynchronously via the **ARQ** worker queue, emitting structured `AuditEvent` records upon completion.

---

## 8. Development & Deployment Topologies

### Local Development Topology
```text
docker-compose.yml
├── frontend (React + Vite dev server on port 3000)
├── backend  (FastAPI Uvicorn reloader on port 8000)
├── postgres (PostgreSQL 16 DB on port 5432)
└── redis    (Redis 7 ARQ queue & pub/sub on port 6379)
```

### Production Enterprise Topology
```text
                     [ Load Balancer / Ingress ]
                                  │
                  ┌───────────────┴───────────────┐
                  ▼                               ▼
       [ Control Plane Pod 1 ]         [ Control Plane Pod 2 ]
                  │                               │
       ┌──────────┴──────────┐         ┌──────────┴──────────┐
       ▼                     ▼         ▼                     ▼
[ PostgreSQL DB ]     [ Redis Cache ] [ Agent Host 1 ]   [ Agent Host 2 ]
```
