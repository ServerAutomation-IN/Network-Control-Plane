# ADR-004: Production Enhancements — Task Queue, Observability, Secret Encryption & State Management

**Status:** Accepted  
**Date:** 2026-10-05  
**Product Name:** Network Control Plane  

---

## 1. Context & Rationale

As the **Network Control Plane** moves from architecture definition to implementation, production-grade requirements dictate enhancements in four key operational areas:

1. **Host Secret Security (TLS Certificates / API Tokens):** Remote provider host daemons require TLS certificates (`ca.pem`, `cert.pem`, `key.pem`) or API keys. Storing these credentials in plaintext in PostgreSQL or configuration files is an unacceptable security vulnerability.
2. **Background Task & Job Execution Resilience:** Long-running operations (multi-host fleet discovery, subnet pruning, drift reconciliation) require a resilient asynchronous queue with automatic retries, rate limiting, and execution state tracking.
3. **Control Plane Telemetry & Observability:** Operating a control plane requires standard Prometheus metrics to monitor inventory sync latency, active host counts, SSE event delivery rate, and job failure rates.
4. **Client-Side Server-State & Multi-Layout Graph Rendering:** Managing backend inventory state on the frontend requires automatic cache invalidation when SSE events fire. Furthermore, visualizing complex topologies requires both hierarchical (ELK.js) and directed (Dagre) layout engines.

---

## 2. Architecture Decisions

### Decision 1: Cryptographic Secret Encryption (`cryptography` / Fernet)
- **Choice:** Use `cryptography.fernet` symmetric field-level encryption for storing host TLS certificates and secret credentials in PostgreSQL.
- **Benefit:** Protects sensitive TLS certificates at rest; decrypts credentials in-memory only when provider adapters establish host connections.

### Decision 2: Async Redis Task Queue (`ARQ`)
- **Choice:** Use **ARQ** (Async Redis Queue) alongside FastAPI.
- **Benefit:** Provides lightweight, high-performance async job execution on Redis with native retry support, timeout controls, and job status persistence.

### Decision 3: Prometheus Telemetry (`prometheus-fastapi-instrumentator`)
- **Choice:** Integrate `prometheus-fastapi-instrumentator` in the FastAPI backend to expose standard `/metrics` endpoints.
- **Benefit:** Enables out-of-the-box monitoring for inventory synchronization duration, REST endpoint latency, and job error counts.

### Decision 4: Frontend Server-State Management (`@tanstack/react-query`)
- **Choice:** Adopt **TanStack React Query** (`@tanstack/react-query`) for fetching and caching backend API server state.
- **Benefit:** Handles background query polling, automatic cache invalidation upon receiving SSE WebSocket events, and deduplication of API requests.

### Decision 5: Multi-Layout Graph Engine (`@dagrejs/dagre` + `ELK.js`)
- **Choice:** Integrate **Dagre** alongside **ELK.js** for React Flow graph layouts.
- **Benefit:** ELK.js handles complex layered graphs, while Dagre provides fast, deterministic layouts for standard directed network dependencies.

---

## 3. Impact & Alignment

- **Blueprint Alignment:** Directly strengthens Architecture Invariants A4 (API Socket Isolation) and A6 (Immutable Audit Trail).
- **Zero Breaking Changes:** Enhancements are additive and seamlessly integrate into the existing FastAPI + React + PostgreSQL stack.
