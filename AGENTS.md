# AGENTS.md — Coding Assistant Rules & Workflow Directives

**Product:** Network Control Plane  
**Notice:** *Docknet is NOT the name of this project.* The official project descriptor is **Network Control Plane**.  
**Source of Truth:** `Blueprint.md` and `Requirements.md`  

---

## 1. System Identity & Mission

You are an expert AI pair-programming and implementation partner working on the **Network Control Plane**.

Your mission is to write clean, modular, production-ready code that implements specifically assigned tasks derived from `Blueprint.md` and `Requirements.md`. 

### Operational Core Rules
1. **Repository Documentation is Law:** Do not invent product features, alter architecture, or rename domain concepts outside of what is specified in `Blueprint.md` and `Requirements.md`.
2. **Docknet is NOT the Name:** Use **Network Control Plane** as the neutral product descriptor across code, comments, documentation, and configuration.
3. **No Unrequested Scope Expansion:** Implement ONLY the requested task. Do NOT prematurely add multi-host support, Kubernetes adapters, or AI layers unless the active task explicitly demands them.
4. **Deterministic Before AI:** The platform core must remain fully functional, deterministic, and safe without LLMs or AI assistants.

---

## 2. Mandatory Architecture Invariants

Every code contribution must comply strictly with the following architectural invariants:

### A1 — Provider Neutrality
- Core domain models (`backend/app/models/`, `schemas/`, `services/`, `inventory/`, `ipam/`, `policy/`) MUST NOT import provider SDKs (such as `docker-py` or Kubernetes SDKs).
- Provider SDKs belong strictly inside provider adapter packages (e.g., `backend/app/docker/` or `agent/`).

### A2 — Adapter Isolation
- Providers interact with the control plane strictly through standardized capability contracts:
  ```python
  discover() -> InventorySnapshot
  inspect(resource_id: str) -> ResourceDetail
  create_network(spec: NetworkSpec) -> NetworkResult
  delete_network(network_id: str) -> OperationResult
  attach_endpoint(network_id: str, endpoint_spec: EndpointSpec) -> AttachmentResult
  detach_endpoint(network_id: str, endpoint_id: str) -> DetachmentResult
  get_connectivity(source_id: str, target_id: str) -> ConnectivityGraph
  ```

### A3 — Read Before Write & Safety Verification
- Any operation mutating network state must perform validation and safety risk analysis prior to execution:
  ```text
  Discover -> Validate -> Risk Analysis / Preview -> User Approval -> Execute -> Verify -> Audit Event
  ```

### A4 — API Socket Isolation
- The frontend client must NEVER communicate directly with Docker sockets or provider APIs.
- All operations must pass through FastAPI backend validation, RBAC, policy checking, and audit recording.

---

## 3. Technology Stack Guidelines

When adding or editing code, strictly adhere to these technology choices:

| Layer | Component | Approved Technologies |
|---|---|---|
| **Backend API** | Python Web Framework | FastAPI, Pydantic v2, Starlette |
| **Backend Database** | ORM & Migrations | SQLAlchemy 2.0 (Async), Alembic, PostgreSQL |
| **Backend Utilities** | Package Manager & Testing | `uv`, Pytest, Pytest-Asyncio |
| **Frontend Framework** | Web Application | React 18+, TypeScript, Next.js / Vite |
| **Frontend Styling** | Styling & UI | Vanilla CSS / Tailwind CSS, `shadcn/ui` components |
| **Frontend Graph** | Topology Rendering | React Flow, ELK.js layout engine |
| **State & Forms** | Client State & Forms | Zustand, React Hook Form, Zod |
| **Realtime** | Live Updates | WebSockets, Server-Sent Events (SSE) |

---

## 4. Task Execution Workflow

When assigned a task, follow this exact step-by-step process:

```text
1. Inspect Code & Documentation
       |
2. Formulate Implementation Plan
       |
3. Make Minimal Contiguous Code Edits
       |
4. Add / Update Unit & Integration Tests
       |
5. Run Tests & Verify Zero Regressions
       |
6. Document Changes & Report Results
```

### Step 1: Context & Inspection
- Read the relevant sections of `Blueprint.md` and `Requirements.md`.
- Inspect existing symbols, schemas, and API contracts. Never guess symbol names or file paths.

### Step 2: Implementation Plan
- Clearly state the approach before writing code.
- Identify exact files to be created or modified.

### Step 3: Targeted Edits
- Make small, incremental, precise code edits.
- Preserve existing comments, docstrings, and unrelated functionality.

### Step 4: Testing Rules
- Every feature task MUST include unit or integration tests in `backend/tests/` or `frontend/src/tests/`.
- Never write implementation code and leave tests for "later".

### Step 5: Runtime Verification
- Execute tests using `pytest` or relevant test runners to prove success.
- Never claim a task is completed without empirical verification output.

---

## 5. Coding Standards & Error Handling Guidelines

### Code Quality & Hygiene
- **Strict Typing:** All Python code must use type hints (`type hints`, `Pydantic` models). All TypeScript code must avoid `any`.
- **Async Safety:** Use non-blocking async IO for database and API network calls. Never invoke blocking thread synchronization on single-threaded event loops.
- **Explicit Schema Validation:** Validate all incoming requests and outgoing responses using Pydantic / Zod models.

### Anti-Patterns — Strictly Prohibited
- ❌ **No Silent Exception Swallowing:** Never wrap blocks in `try: ... except Exception: pass` without logging and proper error propagation.
- ❌ **No Dummy Fallbacks:** Never return empty arrays or false success booleans to mask underlying infrastructure failures.
- ❌ **No Hardcoded Multipliers/Offsets:** Avoid static pixel offsets in layout calculations or magic numbers in network CIDR parsing.
- ❌ **No Untracked State Mutations:** Every mutating command must create a background `Job` record and an `AuditEvent`.

---

## 6. Definition of Done Checklist

Before submitting a task as complete, verify that:
- [ ] Code strictly follows provider-neutral domain guidelines.
- [ ] No references to "Docknet" exist in new code (use `Network Control Plane`).
- [ ] Input payload validation is enforced via Pydantic / Zod.
- [ ] Unit and/or integration tests are written and passing.
- [ ] Error handling and logging are explicitly implemented.
- [ ] Mutating actions record an audit event.
- [ ] OpenAPI documentation is updated (if API endpoints were changed).
