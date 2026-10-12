# Changelog

All notable changes to **Network Control Plane** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [v1.0.0-GA] - 2026-10-11

### Initial General Availability (GA) Release

**Network Control Plane v1.0.0-GA** marks the first enterprise-grade production release of our provider-neutral platform for application and workload networking. This release delivers unified infrastructure discovery, interactive topology visualization, IP address management (IPAM), declarative governance and policy enforcement, GitOps drift reconciliation, zero-trust secrets integration, and human-in-the-loop agentic AI assistance.

### Added

#### 1. Discovery & Provider Adapters Engine
- **Provider-Neutral Architecture (Invariants A1 & A2):** Strict separation between core domain models and provider runtime SDKs.
- **Docker Engine & Docker Swarm Adapter:** Live inspection of networks (`bridge`, `overlay`, `macvlan`, `host`), subnets, gateways, and container workload endpoints.
- **Extended Runtime Adapters:** Initialized capability adapters for Podman, Cilium eBPF CNI, AWS VPC (`boto3`), Azure VNet, and GCP VPC.
- **Dynamic Provider Factory:** Dynamic adapter resolution based on host configuration (`ProviderFactory.get_adapter()`).
- **Fleet Synchronization Service:** Periodic inventory aggregation and host status tracking (`ONLINE`, `UNREACHABLE`, `DEGRADED`).

#### 2. Interactive Topology Graph Visualization
- **React Flow & ELK.js Graph Engine:** High-performance layered graph layout rendering containers, bridges, overlays, and cloud VPCs.
- **Side Panel Inspection:** Detailed inspection drawer displaying network driver options, container IP allocations, labels, and gateway configs.
- **Real-Time Live Updates:** Server-Sent Events (SSE) and WebSocket streams broadcasting topology mutation events.
- **Interactive Controls:** Zoom, pan, search filtering by container name, network label, or environment tag.

#### 3. IP Address Management (IPAM) Engine
- **Capacity & Density Analytics:** Real-time calculation of subnet capacity, used IPs, available host slots, and utilization percentage.
- **CIDR Overlap & Conflict Detection:** Automatic cross-network conflict analysis identifying overlapping IPv4 subnets and gateway collisions before allocation.
- **Static IP Assignment Validation:** Pre-assignment verification ensuring requested IP addresses are within subnet bounds and unallocated.

#### 4. Safety Risk Analysis & Governance Engine
- **Pre-Execution Risk Assessment (Invariant A3):** Automated risk tier evaluation (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) with blast-radius detection before mutating actions.
- **Declarative Governance Policy Rules:** Configurable policies enforcing allowed network drivers, approved CIDR ranges, required container labels, and internal-only isolation.
- **Role-Based Access Control (RBAC):** Strict permissions model (`Administrator`, `Operator`, `Viewer`) with JSON Web Token (JWT) enforcement.

#### 5. GitOps Reconciliation & Background Mutation Queue
- **Declarative Spec Format:** YAML specification format (`network-control-plane/v1`) defining desired network states.
- **Drift Detection Engine:** 3-way diff comparison between actual runtime state and desired declarative GitOps manifests.
- **Reconciliation Plan & Approval Flow:** Human approval requirement before applying drift remediation.
- **ARQ / Redis Background Task Queue:** Non-blocking async mutation execution with persistent `Job` tracking and structured `AuditEvent` history.

#### 6. Enterprise Secrets & Key Vault Integration
- **Zero-Trust Credential Resolution:** Dynamic URI scheme parsing for secrets (`vault://`, `aws-secret://`, `azure-vault://`).
- **HashiCorp Vault KV Adapter:** Secure secret retrieval from Vault KV v1 and v2 engines.
- **Cloud Key Vaults:** Adapters for AWS Secrets Manager and Azure Key Vault.
- **Local AES-256 Fernet Encryption:** Symmetric encryption at rest for stored credentials and TLS host certificates.

#### 7. Governed Human-in-the-Loop Agentic AI
- **LangGraph Diagnostic Agent:** Multi-step agentic graph diagnosing connectivity failures and packet reachability paths.
- **Natural Language Inventory Queries:** Search hosts, networks, and containers using plain English.
- **Mandatory Approval Modal:** Strict human verification requirement before executing AI-generated remediation proposals.
- **Comprehensive AI Audit Trail:** Prompt, reasoning trace, proposed payload, and approving user logged to immutable audit records.

#### 8. Enterprise Identity, Telemetry & Documentation
- **SSO Integration:** OpenID Connect (OIDC) and SAML 2.0 authentication support.
- **Outbound Webhooks:** HMAC SHA-256 signed event dispatchers for third-party alerts.
- **Prometheus Telemetry:** Native `/metrics` endpoint instrumented via `prometheus-fastapi-instrumentator`.
- **Production Documentation:** Complete Administrator Guide, User Guide, Blueprint, Architecture Specification, and ADRs.

---

[v1.0.0-GA]: https://github.com/ServerAutomation-IN/Network-Control-Plane/releases/tag/v1.0.0-GA
