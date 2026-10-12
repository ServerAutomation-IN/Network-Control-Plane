# Network Control Plane — Product Requirements Document (PRD)

**Status:** Draft / Active  
**Product Name:** Network Control Plane (Neutral Working Title — *Docknet is NOT the name*)  
**Tagline:** Visualize. Manage. Validate. Govern. Automate Workload Networking.  
**Document Version:** 1.0  
**Blueprint Reference:** `Blueprint.md` (v2.0)  

---

## 1. Executive Summary & Vision

The **Network Control Plane** is an open-source, extensible, and provider-neutral control plane for modern application and workload networking. 

It provides unified discovery, topology visualization, IP address management (IPAM), policy enforcement, drift detection, desired-state reconciliation, and safe automation across heterogeneous infrastructure.

### Core Philosophy & Positioning
- **Provider-Neutral Core:** The core domain model abstracts concepts like `Network`, `Endpoint`, `Workload`, `Host`, `Subnet`, `Policy`, and `Drift`. Runtimes (Docker, Kubernetes, Podman, Cloud VPCs) are integrated strictly via provider adapters.
- **Docker as First Adapter:** Docker Engine is the initial supported provider to validate the platform architecture, but Docker is **not** the product definition or domain boundary.
- **Operational Discipline:** Every mutating action follows **Read-Before-Write**, **Validation**, **Preview**, **Execution**, **Verification**, and **Audit**.
- **Deterministic AI Grounding:** AI assists with diagnostics, natural language queries, and remediation proposals, but execution is governed by deterministic, human-approved actions.

---

## 2. Architectural Invariants

All requirements must comply with the following architectural constraints:

1. **A1 — Provider Neutrality:** Core domain models must not directly import or depend on provider SDKs (e.g., Docker SDK, Kubernetes client).
2. **A2 — Adapter Isolation:** Provider-specific APIs, schemas, and runtime behaviors must remain isolated inside adapter modules.
3. **A3 — Capability Discovery:** The control plane must query provider capabilities (`discover()`, `inspect()`, `get_connectivity()`, etc.) before exposing actions.
4. **A4 — Source of Truth:** Underlying infrastructure runtimes (e.g., Docker Engine) remain the authoritative runtime state. The control plane manages inventory, desired state, policy, and audit metadata.
5. **A5 — Safe Mutability:** Destructive operations (e.g., deleting networks, disconnecting workloads) require mandatory dependency and risk impact analysis before execution.

---

## 3. Target Personas & Use Cases

### Personas
- **DevOps Engineer:** Needs clear visibility into container networks, cross-container connectivity troubleshooting, and static IP allocation.
- **Platform Engineer:** Needs policy governance, multi-host network inventory management, RBAC, drift detection, and GitOps workflows.
- **Infrastructure Administrator:** Needs centralized management across hosts, IP conflict detection, safe network deletion, and audit logging.
- **Developer:** Needs to understand application service topology and diagnose service-to-service connectivity issues easily.

---

## 4. Functional Requirements (FR)

### Epic 1: Infrastructure & Runtime Discovery (MVP-1)
- **FR-1.1 Host Registration:** Register single or multiple provider hosts (starting with Docker Engine local/remote endpoints).
- **FR-1.2 Network Discovery:** Discover existing provider networks, subnets, gateways, scopes, drivers, internal flags, and labels.
- **FR-1.3 Workload & Endpoint Discovery:** Discover running workloads (containers) and their attached network endpoints, IP allocations, and MAC addresses.
- **FR-1.4 Inventory Synchronization:** Support periodic background synchronization and event-driven updates (e.g., Docker Engine events API).

### Epic 2: Safe Network Management (MVP-2)
- **FR-2.1 Safe Network Creation:** Multi-step wizard to create networks with validated CIDR subnets, gateways, IP ranges, driver options, and labels.
- **FR-2.2 Dependency-Aware Network Deletion:** Perform safety analysis prior to network deletion (checking attached workloads, active services, Compose references) and display a clear risk score.
- **FR-2.3 Endpoint Attachment/Detachment:** Safely connect or disconnect containers to/from networks with optional static IP assignment.
- **FR-2.4 Candidate Pruning:** Identify unused or orphaned networks across managed hosts with low/medium/high risk ratings.

### Epic 3: Interactive Topology Visualization (MVP-3)
- **FR-3.1 Network Graph Rendering:** Render real-time interactive graphs displaying Hosts, Networks, and Workloads/Containers as nodes and connections as edges using React Flow and ELK layout engine.
- **FR-3.2 Topology Interaction:** Support pan, zoom, node selection, side-panel inspection, filtering (by driver, scope, environment, host), and search.
- **FR-3.3 Live Updates:** Reflect runtime connection changes on the graph in near real-time via WebSockets / Server-Sent Events (SSE).

### Epic 4: IP Address Management — IPAM (MVP-4)
- **FR-4.1 Subnet & CIDR Tracking:** Track allocated CIDR blocks, subnets, gateways, reserved pools, and IP utilization percentages per network.
- **FR-4.2 Conflict Detection:** Automatically detect overlapping CIDR blocks, duplicate IP allocations, and gateway mismatches across managed hosts.
- **FR-4.3 Allocation Validation:** Validate proposed static IPs and subnets before submitting network creation requests to provider runtimes.

### Epic 5: Multi-Host & Fleet Foundation (MVP-5)
- **FR-5.1 Centralized Fleet Inventory:** Aggregate networks, subnets, and endpoints across multiple provider hosts grouped by environment (e.g., Dev, Staging, Prod).
- **FR-5.2 Provider Host Agent Protocol:** Establish secure communication channels between the central control plane and remote host agents (`network-control-plane-agent`).

### Epic 6: Governance, Policy & Audit (MVP-6)
- **FR-6.1 Policy Definition Engine:** Evaluate network definitions against declarative rules (e.g., allowed/forbidden drivers, required labels, approved CIDR ranges).
- **FR-6.2 Compliance Reporting:** Mark networks as compliant or non-compliant with detailed failure reasons.
- **FR-6.3 Role-Based Access Control (RBAC):** Enforce permissions for read-only vs. read-write vs. administrative network operations.
- **FR-6.4 Immutable Audit Logging:** Record full audit history (`who`, `what`, `when`, `where`, `before_state`, `after_state`, `result`) for every mutation.

### Epic 7: Desired-State, Drift Detection & GitOps (MVP-7)
- **FR-7.1 Declarative State Definition:** Support declarative YAML schemas representing desired network topology and configuration.
- **FR-7.2 Drift Engine:** Compare actual runtime inventory against desired state files and flag configuration drifts.
- **FR-7.3 Reconciliation Workflow:** Generate structured execution plans to fix drift, requiring human approval before applying changes.

### Epic 8: Human-in-the-Loop Agentic AI (MVP-8)
- **FR-8.1 Natural Language Querying:** Query inventory, topology, and IPAM states via plain text (e.g., *"Show all networks in production with >80% utilization"*).
- **FR-8.2 Automated Diagnostics:** Analyze service reachability and connectivity failures using graph reasoning and infrastructure state.
- **FR-8.3 Governed Remediation:** Propose actionable remediation steps (e.g., adding container to bridge network) with strict Human-in-the-Loop (HITL) approval gates prior to execution.

---

## 5. Non-Functional Requirements (NFR)

### Performance & Scalability
- **NFR-1.1 Synchronization Overhead:** Initial host synchronization must complete within < 3 seconds for hosts with up to 100 networks and 500 containers.
- **NFR-1.2 Topology Render Performance:** Interactive graph must maintain 60 FPS rendering speed for up to 1,000 nodes/edges.
- **NFR-1.3 API Latency:** REST API response time for inventory queries must be < 200ms at p95.

### Security & Compliance
- **NFR-2.1 Provider API Isolation:** Web UI/Frontend must NEVER communicate directly with Docker Engine or provider sockets. All requests route through the FastAPI control plane backend.
- **NFR-2.2 Strict Input Validation:** All API inputs, driver options, and CIDR strings must be strictly validated via Pydantic/Zod schemas to prevent command injection.
- **NFR-2.3 Transport Security:** All inter-component communications (Server-to-Agent, Frontend-to-Backend) must support TLS 1.3 encryption.

### Reliability & Operations
- **NFR-3.1 Transactional Operations:** Network mutation tasks must run as background jobs with explicit status tracking (`PENDING`, `RUNNING`, `SUCCESS`, `FAILED`, `ROLLED_BACK`).
- **NFR-3.2 Resilience:** Loss of connection to a provider host must flag the host as `UNREACHABLE` without crashing the control plane service or corrupting local database state.

---

## 6. MVP Scope & Release Strategy

| Phase | Milestone Name | Key Target Features |
|---|---|---|
| **MVP-0** | Foundation | Repo setup, Docker Compose dev environment, FastAPI backend, React frontend, PostgreSQL DB, CI pipeline. |
| **MVP-1** | Discovery | Single Docker host integration, network/container inventory discovery and listing. |
| **MVP-2** | Management | Network creation, deletion with safety checks, container connect/disconnect, audit log. |
| **MVP-3** | Visual Topology | React Flow + ELK interactive topology graph with real-time refresh. |
| **MVP-4** | IPAM | CIDR tracking, subnet utilization, and cross-network overlap/conflict detection. |
| **MVP-5** | Multi-Host | Fleet discovery across multiple Docker hosts and host agent protocol. |
| **MVP-6** | Governance | Declarative policy enforcement, compliance dashboard, and RBAC. |
| **MVP-7** | Drift & GitOps | Declarative YAML state, drift detection engine, plan/apply reconciliation. |
| **MVP-8** | Agentic AI | LangGraph agent integration, natural language queries, controlled remediation. |

---

## 7. Definition of Done (DoD)

A requirement or task is considered complete only when:
1. Code is fully implemented according to architectural invariants.
2. Unit tests and integration tests pass with required coverage.
3. API endpoints are documented with OpenAPI schemas.
4. Input validation and error handling are verified.
5. Audit event emission is verified for mutating actions.
6. Documentation in `docs/` and `Blueprint.md` alignment is maintained.
7. CI pipeline completes cleanly with no linting errors or type mismatches.
