# Network Control Plane

> **Visualize. Manage. Validate. Govern. Automate Workload Networking.**

[![Release Version](https://img.shields.io/badge/Release-v1.0.0--GA-brightgreen.svg)](https://github.com/ServerAutomation-IN/Network-Control-Plane/releases/tag/v1.0.0-GA)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![CI Pipeline](https://github.com/ServerAutomation-IN/Network-Control-Plane/actions/workflows/ci.yml/badge.svg)](https://github.com/ServerAutomation-IN/Network-Control-Plane/actions/workflows/ci.yml)
[![Security Compliance](https://img.shields.io/badge/Security-Zero--Trust%20Vault%20%7C%20RBAC-blue.svg)](SECURITY.md)
[![Documentation](https://img.shields.io/badge/Docs-v1.0.0--GA%20Ready-blueviolet.svg)](docs/README.md)

The **Network Control Plane** is an enterprise-grade, open-source, and provider-neutral platform for application and workload networking. It delivers unified infrastructure discovery, interactive topology graph visualization, IP address management (IPAM), policy governance, automated GitOps drift reconciliation, enterprise secrets integration, and human-in-the-loop agentic AI assistance across multi-cloud and container environments.

---

## 🏛️ System Architecture Overview

```text
               ┌─────────────────────────────────────────────────────────────┐
               │                React 18 / Vite Web Dashboard                │
               │  (Topology Canvas, IPAM, Policy, GitOps, Host Onboarding)   │
               └──────────────────────────────┬──────────────────────────────┘
                                              │ REST API / WebSockets / SSE / Webhooks
                                              ▼
               ┌─────────────────────────────────────────────────────────────┐
               │              FastAPI Control Plane API Gateway              │
               │   (RBAC, OIDC/SAML SSO, Cloud Ingestion Webhooks, Audit)    │
               └──────┬───────────────────────┬──────────────────────┬───────┘
                      │                       │                      │
                      ▼                       ▼                      ▼
┌───────────────────────────┐   ┌──────────────────────────┐   ┌──────────────────────────┐
│ Pluggable Provider Engine │   │   GitOps & Policy Engine │   │ Enterprise Secrets Engine│
│ ┌───────────────────────┐ │   │ ┌──────────────────────┐ │   │ ┌──────────────────────┐ │
│ │ Container & CNI:      │ │   │ │ Git Sync (GH/GL/BB)  │ │   │ │ HashiCorp Vault      │ │
│ │ • Docker Engine/Swarm │ │   │ │ Drift Reconciliation │ │   │ │ AWS Secrets Manager  │ │
│ │ • Podman / CRI-O      │ │   │ │ Declarative YAML     │ │   │ │ Azure Key Vault      │ │
│ │ • Kubernetes / Cilium │ │   │ └──────────────────────┘ │   │ │ Local Fernet AES-256 │ │
│ ├───────────────────────┤ │   └─────────────┬────────────┘   │ └──────────────────────┘ │
│ │ Hyperscale Cloud VPC: │ │                 │                └─────────────┬────────────┘
│ │ • AWS VPC (boto3)     │ │                 ▼                              │
│ │ • Azure VNet          │ │   ┌──────────────────────────┐                 │
│ │ • GCP Cloud VPC       │ │   │ Redis / ARQ Worker Queue │                 │
│ ├───────────────────────┤ │   │ (Async Mutation Engine)  │                 │
│ │ Hypervisors & HCI:    │ │   └─────────────┬────────────┘                 │
│ │ • VMware vSphere      │ │                 │                              ▼
│ │ • Microsoft Hyper-V   │ │                 │                ┌──────────────────────────┐
│ │ • Nutanix AHV (Prism) │ │                 │                │ Host Agent & Collectors  │
│ ├───────────────────────┤ │                 │                │ ┌──────────────────────┐ │
│ │ Cloud Event Webhooks: │ │                 │                │ │ Bidirectional WS     │ │
│ │ • AWS EventBridge/SNS │ │                 │                │ │ Linux Netlink/Bridge │ │
│ │ • Azure Event Grid    │ │                 │                │ │ Hyper-V vSwitch      │ │
│ │ • GCP Cloud Pub/Sub   │ │                 │                │ │ Docker/Podman Engine │ │
│ └───────────────────────┘ │                 │                │ └──────────────────────┘ │
└──────────────┬────────────┘                 │                └─────────────┬────────────┘
               │                              ▼                              │
               │                ┌──────────────────────────┐                 │
               └───────────────►│ PostgreSQL 16 DB Store   │◄────────────────┘
                                │ (Inventory, Jobs, Audit) │
                                └──────────────────────────┘
```

---

## ✨ Key Platform Features

- **🔍 Unified Infrastructure Discovery:** Automatically inspect networks, subnets, gateways, and workload endpoints across Docker Engine, Swarm, Podman, Kubernetes/Cilium, AWS VPC, Azure VNet, GCP Cloud VPC, VMware vSphere, Microsoft Hyper-V, Nutanix AHV, and Linux host bridges.
- **🗺️ Interactive Topology Canvas:** Render container and workload network graphs using React Flow with ELK.js layout engines, featuring pan, zoom, real-time WebSocket/SSE live updates, and side-panel inspection.
- **🔢 IP Address Management (IPAM):** Real-time subnet capacity tracking, allocation density, static IP validation, and automatic cross-network CIDR overlap / gateway conflict detection.
- **🛡️ Governance & Policy Engine:** Enforce declarative governance rules (approved driver list, CIDR boundaries, required label metadata, naming conventions) and RBAC roles (`Administrator`, `Operator`, `Viewer`).
- **⚡ Safety Risk Analysis:** Pre-execution safety evaluation prior to network mutations (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) to prevent accidental downtime.
- **🔄 GitOps & Desired-State Sync:** Continuous reconciliation of declarative YAML state files (`network-control-plane/v1`) from Git repositories (GitHub, GitLab, Bitbucket) with background task execution queues.
- **☁️ Real-Time Cloud Ingestion Webhooks:** Ingest push events from AWS EventBridge/SNS, Azure Event Grid, GCP Cloud Pub/Sub, and VMware vSphere for instant drift-free inventory delta synchronization.
- **🚀 Host Agent & Pluggable Runtimes:** Lightweight host agent daemon (`network-control-plane-agent`) with bidirectional WebSocket command dispatch and pluggable collectors for Linux Netlink, Hyper-V vSwitch, Docker, and Podman.
- **🔑 Enterprise Secrets & Key Vault Integration:** Zero-trust credentials resolution supporting dynamic URI references (`vault://`, `aws-secret://`, `azure-vault://`) via HashiCorp Vault, AWS Secrets Manager, Azure Key Vault, and Local Fernet AES-256.
- **🔐 Enterprise SSO & Outbound Webhooks:** OIDC and SAML 2.0 authentication integration (Okta, Entra ID, Keycloak) paired with HMAC SHA-256 signed outbound webhook dispatchers.
- **🤖 Governed AI Diagnostics:** Automated topology reachability analysis and natural language queries, protected by mandatory human-in-the-loop approval gates.

---

## 💻 Supported Infrastructure Matrix

| Category | Supported Platforms & Integrations |
|---|---|
| **Container Runtimes** | Docker Engine 24.0+, Docker Swarm Overlay, Podman 4.0+, Containerd / CRI-O |
| **Kubernetes & CNI** | Kubernetes 1.28+, OpenShift, Cilium eBPF CNI, Linux Bridge, Macvlan, Overlay |
| **Hyperscale Cloud VPCs** | AWS VPC, Azure VNet, Google Cloud Platform (GCP) VPC |
| **Hypervisors & Private Cloud** | VMware vSphere 7.0+/8.0+, Microsoft Hyper-V / SCVMM, Nutanix AHV (Prism Element/Central) |
| **Host Agent & OS Engines** | Bidirectional Python agent (`network-control-plane-agent`), Linux Netlink/Bridge, Hyper-V vSwitch, Docker/Podman collectors |
| **Cloud Event Ingestion** | AWS EventBridge & SNS, Azure Event Grid, GCP Cloud Pub/Sub, VMware vSphere Events |
| **Secrets Managers** | HashiCorp Vault (KV v1/v2), AWS Secrets Manager, Azure Key Vault, Local Fernet AES-256 |
| **Enterprise Identity** | OpenID Connect (OIDC), SAML 2.0 (Okta, Microsoft Entra ID, Keycloak) |
| **Git Repositories** | GitHub, GitLab, Bitbucket Cloud / Server |
| **Database & Queue** | PostgreSQL 16+, Redis 7+ (ARQ async task queue) |

---

## 🚀 Quickstart Guide

### Prerequisites
- Docker Engine 24.0+ & Docker Compose v2+
- Python 3.12+ (with `uv` package manager)
- Node.js 18+ & npm

### Running the Stack via Docker Compose

```bash
# Clone the repository
git clone https://github.com/ServerAutomation-IN/Network-Control-Plane.git
cd Network-Control-Plane

# Launch multi-container production stack
docker compose -f deployment/docker-compose.yml up -d
```

### Accessing Platform Endpoints
- **Web UI Dashboard:** `http://localhost:3001` (Docker Compose) or `http://localhost:3000` (Dev server)
- **Interactive OpenAPI (Swagger) Docs:** `http://localhost:8000/docs`
- **ReDoc API Documentation:** `http://localhost:8000/redoc`
- **Prometheus Telemetry Metrics:** `http://localhost:8000/metrics`
- **PostgreSQL Database:** `localhost:5432`

---

## ⚙️ Environment Variables Directory

| Parameter | Description | Default |
|---|---|---|
| `DATABASE_URL` | PostgreSQL async connection string | `postgresql+asyncpg://postgres:postgres@localhost:5432/network_control_plane` |
| `REDIS_URL` | Redis connection URL for ARQ task queue & caching | `redis://localhost:6379/0` |
| `SECRET_KEY` | Symmetric key for local secret encryption / JWT signing | `change-this-in-production-secret-key-32bytes` |
| `VAULT_ADDR` | HashiCorp Vault server endpoint | `http://127.0.0.1:8200` |
| `VAULT_TOKEN` | HashiCorp Vault access token (or AppRole) | `root` |
| `OIDC_ISSUER` | OIDC Identity Provider issuer URL | `https://auth.example.com/realms/master` |
| `GITOPS_REPO_URL` | Desired-state Git repository URL | `https://github.com/ServerAutomation-IN/network-desired-state.git` |
| `LOG_LEVEL` | Application logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`) | `INFO` |

---

## 📚 Product Documentation Index

Complete production release documentation is organized within the [`docs/`](docs/README.md) directory:

### 📢 Launch & Announcements
- **[v1.0.0-GA Product Launch Announcement](docs/announcements/v1.0.0-GA-Launch-Announcement.md)** — Official technical launch article and product manifesto.

### 📖 Product Release Guides
- **[Deployment & Configuration Guide (Admin Guide)](docs/deployment/Deployment_and_Configuration_Guide.md)** — Administrator guide covering prerequisites, HA cluster deployment, security hardening, database maintenance, and monitoring.
- **[User Guide](docs/user-guide/User_Guide.md)** — Comprehensive user guide covering UI navigation, network creation wizard, safety risk analysis, interactive topology canvas, IPAM conflict resolution, GitOps workflows, SSO, and Key Vault setup.
- **[Okta SSO Configuration Guide](docs/user-guide/Okta_SSO_Configuration_Guide.md)** — Step-by-step administrator guide for Okta OIDC SSO integration and role mapping.

### 🏛️ Product Strategy & Architecture
- **[Product Blueprint](docs/product/Blueprint.md)** — Architectural north star and system specifications.
- **[System Architecture Specification](docs/architecture/Architecture.md)** — System invariants (A1–A4) and sub-component design.
- **[Architecture & Data Flow Diagram](docs/architecture/Network-Control-Plane_Architecture-And-DataFlow-Diagram.drawio.png)** — Visual architecture and component data-flow diagram.
- **[Requirements Document](docs/requirements/Requirements.md)** — Functional and non-functional specifications.
- **[Architecture Decision Records (ADRs)](docs/adr/ADR-001-backend.md)** — Formal architectural decision records (`ADR-001` through `ADR-004`).

### 🗺️ Roadmap & Release History
- **[Release Changelog](CHANGELOG.md)** — Detailed feature and release notes for `v1.0.0-GA`.
- **[Product Roadmap](docs/roadmap/roadmap.md)** — Phase A–H release sequence and expansion strategy.

### 💡 Architectural Improvement Proposals (RFCs)
- **[Proposals Index (docs/proposals/)](docs/proposals/README.md)** — Active and implemented architectural RFCs tracking host agent bidirectional command channels, pluggable runtimes, one-click host onboarding wizard, and developer tooling.


---

## 🔒 Security & Vulnerability Reporting

The **Network Control Plane** enforces zero-trust security guidelines. Do not submit security vulnerabilities via public GitHub issues. Please consult [`SECURITY.md`](SECURITY.md) for confidential security disclosure instructions.

---

## 🤝 Contributing

We welcome community contributions! Please review [`CONTRIBUTING.md`](CONTRIBUTING.md) and [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) before submitting pull requests.

---

## 📄 License

This project is licensed under the Apache License, Version 2.0 - see the [`LICENSE`](LICENSE) file for details.
