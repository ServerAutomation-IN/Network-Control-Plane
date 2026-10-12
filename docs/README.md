# Network Control Plane — Central Documentation Index

Welcome to the central documentation index for **Network Control Plane**, an enterprise-grade, provider-neutral control plane platform for containerized and virtualized workload networking.

---

## 📢 Product Announcements & Release Notes (`docs/announcements/`)

- **[v1.0.0-GA Product Launch Announcement](announcements/v1.0.0-GA-Launch-Announcement.md)** — The flagship technical launch article and product manifesto detailing the problem statement, architectural vision, and capabilities.

---

## 🚀 Product Release & Operations Guides (`docs/deployment/` & `docs/user-guide/`)

- **[Deployment & Configuration Guide (Admin Guide)](deployment/Deployment_and_Configuration_Guide.md)** — Comprehensive Administrator guide covering prerequisites, high availability (HA) deployment, configuration parameters, database maintenance, telemetry, and security hardening.
- **[User Guide](user-guide/User_Guide.md)** — Platform engineer guide covering UI navigation, network creation, safety risk analysis, interactive topology canvas, IPAM conflict resolution, Policy engine, GitOps sync workflows, and enterprise Key Vault configuration.
- **[Okta SSO Configuration Guide](user-guide/Okta_SSO_Configuration_Guide.md)** — Step-by-step administrator guide for Okta OIDC SSO integration, role/group mapping, Just-In-Time (JIT) provisioning, and troubleshooting.

---

## 🏛️ Architecture & System Specifications (`docs/product/` & `docs/architecture/`)

- **[Product Blueprint](product/Blueprint.md)** — Architectural north star, domain invariants, and system capability specifications.
- **[System Architecture Specification](architecture/Architecture.md)** — Architectural invariants (A1–A4), adapter isolation, and end-to-end data flows.
- **[System Architecture & Data Flow Diagram](architecture/Network-Control-Plane_Architecture-And-DataFlow-Diagram.drawio.png)** — Visual architecture and component data-flow diagram.
- **[Functional & Non-Functional Requirements](requirements/Requirements.md)** — Comprehensive requirements document (PRD) and acceptance criteria.
- **[Problem Statement](product/Problem_Statement.md)** — Operational and governance challenges in modern workload networking.
- **[Product Vision](product/vision.md)** — Strategic vision, core pillars, and long-term design objectives.

---

## 🧭 Architectural Decision Records (`docs/adr/`)

- **[ADR-001: Backend Service Framework](adr/ADR-001-backend.md)** — Adoption of Python 3.12, FastAPI, and Pydantic v2.
- **[ADR-002: Relational Store & Asynchronous ORM](adr/ADR-002-database.md)** — Adoption of PostgreSQL 16 and async SQLAlchemy 2.0.
- **[ADR-003: Distributed Host Agent Architecture](adr/ADR-003-agent.md)** — Lightweight host daemon, pluggable collectors, and bidirectional command dispatch.
- **[ADR-004: Observability, Task Queue, & State Sync](adr/ADR-004-observability-taskqueue-state.md)** — Redis, ARQ worker queue, and Prometheus instrumentation.

---

## 🗺️ Product Roadmap (`docs/roadmap/`)

- **[Product Roadmap & Phase Sequence](roadmap/roadmap.md)** — Multi-phase release matrix and capability evolution across Core, Multi-Host, Cloud, and Enterprise Governance.

---

## 💡 Improvement Proposals & RFCs (`docs/proposals/`)

Architectural improvement proposals (RFCs) tracking major platform enhancements, onboarding workflows, and developer hygiene:

- **[Proposals Index (README)](proposals/README.md)** — Overview of all active and implemented improvement proposals.
- **[IMP-01: Host Agent Bidirectional Command Channel](proposals/IMP-01-agent-bidirectional-command-channel.md)** — Real-time agent command polling and remote mutation execution.
- **[IMP-02: Multi-Runtime Pluggable Engine Collectors](proposals/IMP-02-agent-pluggable-runtimes.md)** — Pluggable collectors for Docker, Podman Netavark, Windows Hyper-V, and Linux Bridges.
- **[IMP-03: One-Click Host Onboarding Wizard & Bootstrap Script](proposals/IMP-03-one-click-agent-bootstrap-wizard.md)** — 15-minute ephemeral bootstrap tokens and automated cross-platform installers (`install.sh`, `install.ps1`).
- **[IMP-04: Cloud Event-Driven Ingestion Webhooks](proposals/IMP-04-cloud-event-driven-webhooks.md)** — Real-time cloud VPC subnet and route table sync via webhooks.
- **[IMP-05: Backend Developer Guide & Setup Documentation Enrichment](proposals/IMP-05-backend-developer-guide-enrichment.md)** — Comprehensive developer guide in `backend/README.md`.
- **[IMP-06: Test Coverage, Build, and OS Hygiene Additions](proposals/IMP-06-gitignore-build-test-hygiene.md)** — Preventative ignore rules in `.gitignore`.
- **[IMP-07: Central Documentation Index Cleanup](proposals/IMP-07-docs-readme-clean-index.md)** — Remediation of broken links and clean index consolidation.
- **[IMP-08: Transition to Apache License 2.0](proposals/IMP-08-apache2-patent-protection-license.md)** — Patent protection and retaliation defense under Apache 2.0.
- **[IMP-09: Root README Documentation Index Cleanup](proposals/IMP-09-root-readme-broken-links-cleanup.md)** — Root README links remediation.
- **[IMP-10: Contributing Guide External Contributor Workflow Polish](proposals/IMP-10-contributing-guide-external-polish.md)** — Contributor guidelines and workflow polish.

---

## 📋 Developer & Contributor Directives

- **[Coding Directives & Rules (AGENTS.md)](../AGENTS.md)** — Operational core rules and architectural invariants.
- **[Backend Developer Guide](../backend/README.md)** — Backend local environment setup, testing, and migration workflows.
- **[Contributing Guidelines](../CONTRIBUTING.md)** — Pull request guidelines and code of conduct.
