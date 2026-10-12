# Network Control Plane — Product Blueprint

**Status:** Product Blueprint  
**Working Name:** Network Control Plane (brand name under evaluation)  
**Recommended Naming Direction:** Neutral, platform-independent brand + descriptive product category  
**Tagline:** Visualize. Manage. Validate. Govern. Automate Workload Networking.  
**Document Version:** 2.0  
**MVP Target:** v0.1 — Single Docker Host Network Control Plane

---

# 1. Executive Summary

The product is an open-source web-based **Network Control Plane for modern application infrastructure**.

Its first implementation targets Docker networking, but Docker is intentionally treated as a **provider/adapter**, not as the product's permanent domain boundary.

The platform provides a centralized interface to:

- Discover infrastructure, networks, workloads and endpoints
- Visualize topology and connectivity relationships
- Manage network resources through safe, validated operations
- Understand addressing and IP relationships
- Detect subnet, IP and configuration conflicts
- Safely identify unused or risky resources
- Maintain a complete audit trail
- Manage multiple infrastructure providers over time
- Enforce networking policies and governance
- Detect infrastructure drift
- Support desired-state/GitOps workflows
- Provide an optional Agentic AI layer for diagnosis, recommendations and controlled remediation

Docker Engine remains the source of truth for the Docker implementation. The control plane provides the operational, visualization, governance and automation layer above the underlying infrastructure.

**Strategic rule:** Docker is the first supported platform, not the product definition.

---

# 2. Naming Decision

## Strategic Naming Principle

The product name should **not contain Docker, Kubernetes, AWS, Azure, GCP or another implementation technology**.

The name should remain relevant if the platform expands from Docker to Kubernetes, VMs, cloud networking, enterprise IPAM, network devices or other workload platforms.

### Recommended naming pattern

```text
[Neutral Brand]
        +
Network Control Plane
```

The category descriptor explains what the product does while the brand remains independent of any one technology.

## Current Working Name

### Network Control Plane

For implementation and documentation, use **Network Control Plane** as the neutral working descriptor until a final brand is selected.

The repository can therefore remain temporarily:

```text
network-control-plane/
```

A final brand can be introduced later without forcing an architectural rename.

## Brand Candidates

The following names are intentionally treated as **candidates, not trademark-clearance conclusions**:

| Candidate | Relevance | Strategic fit | Recommendation |
|---|---:|---:|---|
| **NetWeave** | High | High | Avoid — existing products/projects |
| **NetScope** | High | Medium | Avoid — existing network products |
| **NetPilot** | High | Medium | Avoid — active AI/network products |
| **NetFabric** | High | High | Avoid — active AI/network company |
| **NetAxis** | High | High | Avoid — existing networking company |
| **Netora** | High | High | Avoid — active network/AI products |
| **Nexora** | Medium | High | Avoid — heavily used across technology products |
| **Network Control Plane** | Very high | Very high | **Recommended working descriptor** |

**Important:** A final commercial brand should undergo trademark, domain, package/repository and marketplace checks before public launch.

## Brand Strategy

The product should be able to evolve as:

```text
Neutral Brand
    │
    └── Network Control Plane
            │
            ├── Docker Adapter
            ├── Kubernetes Adapter
            ├── Podman / Container Runtime Adapter
            ├── Cloud Network Adapters
            └── Infrastructure / Network Device Adapters
```

This prevents the brand from becoming obsolete when the supported infrastructure expands.

# 3. Product Vision

> Build an open-source, extensible and eventually AI-native **Network Control Plane for modern application infrastructure**.

The platform should make complex workload networking easier to:

- Discover
- Understand
- Visualize
- Design
- Validate
- Manage
- Govern
- Automate
- Reconcile
- Troubleshoot

### First implementation

> **Docker networking**

### Long-term platform direction

> **Container, workload and infrastructure networking**

Docker is the first adapter because it provides a practical, accessible and highly testable starting point. The architecture must not make Docker the permanent domain model.

## Strategic Evolution

```text
                    Network Control Plane
                             |
              +--------------+--------------+
              |              |              |
           Discover       Understand      Control
              |              |              |
        Inventory         Topology        Operations
        Networks          Connectivity    Policy
        Workloads         Dependencies    IPAM
              |              |              |
              +--------------+--------------+
                             |
                       Reconciliation
                             |
                    Desired State / GitOps
                             |
                         Automation
                             |
                      Agentic Intelligence
                             |
                  +----------+----------+
                  |          |          |
               Docker   Kubernetes    Cloud
               Adapter    Adapter    Adapters
```

## Provider-Neutral Core Principle

The domain model must represent concepts such as:

```text
Network
Endpoint
Workload
Host
Address
Subnet
Route
Policy
Connectivity
Topology
Intent
Drift
Operation
Provider
```

Provider-specific implementation details belong behind adapters.

Avoid making the core domain depend directly on concepts such as:

```text
DockerNetwork
DockerContainer
InfrastructureHost
DockerOnlyNetworkOption
```

Instead:

```text
Network
    └── provider_reference
        ├── provider = docker
        ├── provider = kubernetes
        └── provider = cloud
```

## Architectural North Star

```text
             Provider-Neutral Domain
                       |
          +------------+------------+
          |            |            |
       Docker      Kubernetes      Cloud
       Adapter       Adapter      Adapter
          |            |            |
      Docker API    K8s API      Cloud APIs
```

The MVP remains Docker-focused. The architecture is platform-neutral.

# 4. Problem Statement

Docker provides powerful networking primitives, but operating Docker networking becomes difficult as infrastructure grows.

Typical environments contain:

```text
Docker Host 01
  +-- frontend_net
  +-- backend_net
  +-- database_net
  +-- monitoring_net
  +-- containers

Docker Host 02
  +-- frontend_net
  +-- backend_net
  +-- monitoring_net
  +-- containers

Docker Host 03
  +-- ...
```

Operators often rely on:

```text
docker network ls
docker network inspect
docker network create
docker network connect
docker network disconnect
docker network rm
docker network prune
```

The problem is not the absence of Docker commands.

The problem is the absence of a unified operational model.

Operators need answers to questions such as:

- Which containers belong to a network?
- Which applications depend on a network?
- Which networks exist across all Docker hosts?
- Are there overlapping CIDRs?
- Which networks are unused?
- Why cannot container A reach container B?
- Which networks violate organizational policy?
- What changed?
- Is it safe to delete a network?
- What network should a new application use?
- Can the desired network state be represented as code?
- Can changes be reviewed before execution?

---

# 5. Product Positioning

DockNet should **not** be positioned as:

> "Another Docker UI."

It should be positioned as:

> **A Docker Network Control Plane**

Core value proposition:

```text
Discover
   |
Visualize
   |
Understand
   |
Validate
   |
Manage
   |
Govern
   |
Automate
```

Existing Docker management products provide some network functionality. DockNet differentiates through network-centric topology, IPAM, governance, drift and safe automation.

---

# 6. Competitive Landscape

## Docker CLI

Strength:

- Native
- Complete low-level control
- Scriptable

Weakness:

- No centralized visualization
- No topology
- No governance
- No multi-host network control plane
- No high-level safety analysis

---

## Portainer

Strength:

- Broad Docker management
- Network management
- Multi-environment management

Weakness for this product opportunity:

- General-purpose Docker platform rather than a dedicated networking control plane

DockNet should therefore avoid competing on generic container management.

---

## Dockge / Yacht / similar Docker UIs

Strength:

- Lightweight
- Compose-oriented
- Developer-friendly

Weakness:

- Not specialized network control planes

---

## Docker network visualization projects

Strength:

- Topology and visualization

Weakness:

- Usually limited management/governance/IPAM/control-plane capabilities

---

# 7. Target Users

## DevOps Engineer

Needs:

- Network inventory
- Troubleshooting
- Connectivity visibility
- Network management
- IP information

## Platform Engineer

Needs:

- Multi-host management
- Policies
- RBAC
- Audit
- Drift
- Governance

## Infrastructure Administrator

Needs:

- Centralized management
- Safe operations
- Topology
- IPAM
- Troubleshooting

## Developer

Needs:

- Understand application networks
- Understand service connectivity
- Diagnose container connectivity problems

---

# 8. Product Principles

## P1 — Docker remains the source of truth

DockNet operates through Docker APIs.

```text
Docker Engine
      ^
      |
   DockNet
```

DockNet's database stores inventory, metadata, policy and desired-state information, but actual Docker resources remain controlled by Docker.

---

## P2 — Read before write

Every mutating operation should follow:

```text
Discover
  |
Validate
  |
Preview
  |
Approve
  |
Execute
  |
Verify
  |
Audit
```

---

## P3 — Deterministic before AI

The core networking platform must work without an LLM.

AI is added later for:

- Diagnosis
- Explanation
- Recommendations
- Natural-language queries
- Remediation planning

---

## P4 — Destructive actions must be explainable

Before deleting a network, show:

```text
Network: backend-old

Attached containers: 0
Active services: 0
Compose references: 0
Recent activity: none

Risk: LOW

Recommendation:
SAFE TO DELETE
```

---

## P5 — MVP must have a hard boundary

Interesting features must not silently expand the MVP.

Every new feature goes through:

```text
Idea
 |
Feature Proposal
 |
Value / Complexity
 |
+---- MVP?
|      |
YES    NO
|      |
Backlog Future Release
```

---

# 9. Product Scope

## In Scope

- Docker Engine
- Docker Networks
- Docker Containers
- Docker Hosts
- Docker Compose awareness
- Network topology
- IPAM
- Network policies
- Drift detection
- Audit
- RBAC
- Automation
- Agentic AI

## Explicitly Out of Initial Scope

- Kubernetes
- CNI management
- Physical switch management
- Firewall management
- Cloud VPC management
- Service mesh management
- Full network monitoring replacement
- Packet capture platform

These may become future integrations but should not affect the initial product.

---

# 9A. Platform Boundary

## What the Core Platform Owns

The control plane owns:

- Provider abstraction
- Normalized inventory
- Network/workload relationships
- Topology representation
- IPAM intelligence
- Policy evaluation
- Desired state
- Drift detection
- Operation planning
- Approval workflows
- Audit records
- Provider adapter contracts

## What Providers Own

Providers remain authoritative for actual infrastructure state:

- Resource creation/deletion
- Network attachment
- Runtime-specific configuration
- Runtime lifecycle
- Provider-specific connectivity mechanisms

## Adapter Contract

Each provider adapter should expose a normalized capability contract:

```text
discover()
inspect()
create_network()
update_network()
delete_network()
attach_endpoint()
detach_endpoint()
get_connectivity()
watch_events()
validate_capability()
```

Not every provider must implement every capability. Capabilities should be explicitly discoverable.

## Architectural Rule

> **The core domain must not import provider SDKs directly.**

Provider SDKs belong inside adapter/infrastructure modules.

# 10. Core Use Cases

## UC-001 — Discover Docker Host

```text
Add Docker Host
      |
Validate Connection
      |
Collect Metadata
      |
Store Inventory
```

## UC-002 — List Networks

Display:

- Name
- Driver
- Scope
- Subnet
- Gateway
- Container count
- Host
- Status

## UC-003 — Inspect Network

Display:

- Network configuration
- Driver
- Scope
- IPAM
- Containers
- IP addresses
- Labels
- Topology

## UC-004 — Create Network

Wizard:

1. Name
2. Driver
3. IPv4/IPv6
4. Subnet
5. Gateway
6. IP range
7. Internal
8. Attachable
9. Labels
10. Driver options
11. Validation
12. Preview
13. Create

## UC-005 — Connect Container

```text
Select Network
      |
Select Container
      |
Optional Static IP
      |
Validate
      |
Preview
      |
Apply
```

## UC-006 — Disconnect Container

Must show dependency/risk information before execution.

## UC-007 — Delete Network

Must perform safety analysis first.

---

# 11. Core Features

## Feature Group A — Discovery

- Docker host discovery
- Docker version
- OS
- Architecture
- Network discovery
- Container discovery
- Docker events
- Periodic synchronization

## Feature Group B — Network Management

- Create
- Inspect
- Delete
- Connect
- Disconnect
- Prune candidates
- Labels
- Driver configuration

## Feature Group C — Topology

- Interactive graph
- Networks
- Containers
- Hosts
- Relationships
- Search
- Filter
- Highlight
- Real-time updates

## Feature Group D — IPAM

- CIDR
- Subnet
- Gateway
- IP range
- Allocation
- Utilization
- Conflict detection
- Future reservations

## Feature Group E — Governance

- Naming policy
- Driver policy
- CIDR policy
- Label policy
- Environment policy
- Compliance reporting

## Feature Group F — Drift

- Desired state
- Actual state
- Comparison
- Drift detection
- Remediation plan
- Approval
- Apply
- Verification

## Feature Group G — AI

- Natural-language inventory
- Troubleshooting
- Recommendations
- Risk analysis
- Remediation proposals

---

# 12. Provider Networking Model — Docker First

Initial deep support:

```text
bridge
```

Phase 2:

```text
overlay
```

Phase 3:

```text
macvlan
ipvlan
```

Docker network drivers have different operational characteristics. The product should model driver-specific capabilities rather than treating every network identically.

---

# 13. Interactive Topology

Example:

```text
                    frontend_net
                          |
             +------------+------------+
             |            |            |
           nginx       frontend       web
             |
             v
                    backend_net
                          |
                    +-----+-----+
                    |           |
                   api        worker
                    |
                    v
                  db_net
                    |
                    v
                postgres
```

Topology requirements:

- Zoom
- Pan
- Search
- Filter
- Highlight
- Network focus
- Container focus
- IP display
- Host display
- Labels
- Driver
- Dependency relationships
- Real-time refresh

---

# 14. IPAM

Example:

```text
Network: backend

CIDR:
172.20.10.0/24

Gateway:
172.20.10.1

Allocated:
31

Available:
94

Utilization:
24%
```

## Conflict Detection

```text
Network A
172.20.10.0/24

Network B
172.20.10.0/24

STATUS:
CRITICAL — overlapping subnet
```

---

# 15. Connectivity Analysis

User selects:

```text
Source: frontend
Destination: postgres
```

DockNet analyzes:

- Common networks
- Network isolation
- Host relationships
- IP information
- Known topology relationships

Example:

```text
frontend
  |
frontend_net
  X
backend_net
  X
postgres

RESULT:
NOT CONNECTED

Reason:
No shared Docker network.
```

Important:

> Docker network membership does not prove application-level connectivity.

Future versions can support active connectivity probes.

---

# 16. Safe Network Deletion

Example:

```text
Network: old_backend

Attached containers: 0
Active services: 0
Compose references: 0
Last activity: 122 days ago

Risk: LOW

Recommendation:
SAFE TO DELETE
```

The product should make Docker's destructive operations safer by adding context and validation.

---

# 17. Policy Engine

Example policy:

```yaml
policies:

  production:

    allowed_drivers:
      - bridge
      - overlay

    forbidden_drivers:
      - host

    required_labels:
      environment: production
      owner: required

    approved_cidr:
      - 10.100.0.0/16
```

Evaluation:

```text
Network: prod-api

✓ driver
✓ CIDR
✓ environment label
✗ owner label

STATUS:
NON-COMPLIANT
```

---

# 18. Drift Detection

Architecture:

```text
Desired State
     |
     v
Git / YAML
     |
     v
DockNet
     |
     v
Docker
     |
     v
Actual State
     |
     v
Drift Engine
```

Example:

```text
Expected:
backend
CIDR: 10.20.0.0/24

Actual:
backend
CIDR: 10.30.0.0/24

DRIFT DETECTED
```

---

# 19. Desired-State Model

Example:

```yaml
version: docknet/v1

network:
  name: backend

  driver: bridge

  ipam:
    subnet: 10.20.10.0/24
    gateway: 10.20.10.1

  labels:
    environment: production
    owner: payments
```

This becomes the basis for GitOps.

---

# 20. Architecture

# 20A. Architecture Invariants

These are blueprint-level constraints and should be treated as architecture rules.

### A1 — Provider Neutrality

The core domain cannot depend on Docker, Kubernetes or a cloud SDK.

### A2 — Adapter Isolation

Provider-specific APIs, schemas and behavior remain inside provider adapters.

### A3 — Capability Discovery

The control plane must know which operations a provider supports before exposing them to users or automation.

### A4 — Normalized State

The control plane may normalize provider state for analysis and visualization, but it must never silently become the authoritative infrastructure state.

### A5 — Deterministic Execution

AI can reason, explain and propose. Deterministic tools perform validated infrastructure operations.

### A6 — Safe Expansion

Adding a provider must not require rewriting the core domain model.



```text
                         Browser
                            |
                            v
                 +--------------------+
                 | React / TypeScript |
                 +----------+---------+
                            |
                       REST / SSE
                            |
                            v
                 +--------------------+
                 |      FastAPI       |
                 +----------+---------+
                            |
              +-------------+-------------+
              |             |             |
              v             v             v
         Inventory       Policy        Actions
          Service        Engine         Engine
              |             |             |
              +-------------+-------------+
                            |
                      Docker Adapter
                            |
                            v
                    Docker Engine API
```

---

# 21. Backend Technology

Recommended:

| Component | Technology |
|---|---|
| Language | Python |
| API | FastAPI |
| Docker integration | Docker SDK for Python |
| ORM | SQLAlchemy |
| Database | PostgreSQL |
| Validation | Pydantic |
| Migrations | Alembic |
| Cache | Redis |
| Realtime | WebSocket/SSE |
| Testing | Pytest |
| Packaging | uv |
| API | OpenAPI |

---

# 22. Frontend Technology

Recommended:

```text
React
TypeScript
Next.js
Tailwind CSS
shadcn/ui
Zustand
React Hook Form
Zod
React Flow
ELK.js
Recharts
```

React Flow and ELK.js should be used for the topology visualization.

---

# 23. Database Model

Core entities:

```text
users
roles
permissions

docker_hosts

networks
network_subnets
network_options
network_labels

containers
container_networks

network_policies
policy_results

network_snapshots
network_drift

audit_events

jobs
job_events
```

## InfrastructureHost

```text
id
name
endpoint
environment
status
docker_version
os
architecture
last_seen
created_at
updated_at
```

## Network

```text
id
host_id
docker_network_id
name
driver
scope
internal
attachable
ingress
created_at
updated_at
```

## NetworkSubnet

```text
id
network_id
subnet
gateway
ip_range
aux_addresses
ipv6
```

## ContainerNetwork

```text
id
container_id
network_id
ip_address
ipv6_address
mac_address
aliases
```

---

# 24. REST API

Base:

```text
/api/v1
```

## Hosts

```http
GET    /hosts
POST   /hosts
GET    /hosts/{id}
DELETE /hosts/{id}
POST   /hosts/{id}/sync
```

## Networks

```http
GET    /networks
POST   /networks
GET    /networks/{id}
PATCH  /networks/{id}
DELETE /networks/{id}
POST   /networks/{id}/prune
```

## Containers

```http
GET /containers
GET /containers/{id}
```

## Connections

```http
POST   /networks/{id}/containers
DELETE /networks/{id}/containers/{container_id}
```

## Topology

```http
GET /topology
GET /topology/networks/{id}
GET /topology/containers/{id}
```

## IPAM

```http
GET  /networks/{id}/ipam
POST /networks/{id}/ipam/validate
GET  /ipam/conflicts
```

## Policies

```http
GET    /policies
POST   /policies
GET    /policies/{id}
PUT    /policies/{id}
DELETE /policies/{id}
POST   /policies/evaluate
```

## Drift

```http
GET  /drift
GET  /drift/{id}
POST /drift/{id}/plan
POST /drift/{id}/apply
```

---

# 25. UI Information Architecture

```text
DockNet
|
+-- Dashboard
|
+-- Infrastructure
|   +-- Hosts
|   +-- Networks
|   +-- Containers
|
+-- Topology
|
+-- IPAM
|
+-- Policies
|
+-- Drift
|
+-- Jobs
|
+-- Audit
|
+-- Settings
```

---

# 26. Network Detail Screen

```text
Backend

[Overview] [Topology] [Containers] [IPAM]
[Configuration] [Policy] [Drift] [Audit]

Driver       bridge
Scope        local
Subnet       10.20.10.0/24
Gateway      10.20.10.1
Internal     No
Attachable   No

Containers

api
worker
postgres
```

---

# 27. Job Execution Model

Every mutating operation should become a job:

```text
User
 |
 v
API
 |
 v
Validation
 |
 v
Job
 |
 v
Action Engine
 |
 v
Docker API
 |
 v
Verification
 |
 v
Audit
```

Job example:

```text
ID: JOB-000123
Action: CREATE_NETWORK
Status: SUCCESS
Host: docker-prod-01
```

---

# 28. Audit Model

Every mutation should record:

```text
WHO
WHAT
WHEN
WHERE
BEFORE
AFTER
RESULT
```

Example:

```text
User: admin
Action: NETWORK_DELETE
Network: backend-old
Host: docker-prod-01
Result: SUCCESS
Timestamp: 2026-10-04 22:15
```

---

# 29. Security Architecture

Do not allow the frontend to directly control Docker.

```text
Browser
   |
   v
FastAPI
   |
   +-- Authentication
   +-- Authorization
   +-- Validation
   +-- Policy
   +-- Audit
   |
   v
Docker Adapter
   |
   v
Docker Engine
```

For production, move toward:

```text
DockNet Server
      |
      +---- Agent ---- Docker Host 01
      |
      +---- Agent ---- Docker Host 02
      |
      +---- Agent ---- Docker Host 03
```

---

# 30. Provider Host Agent — Docker First

Future component:

```text
docknet-agent
```

Responsibilities:

- Docker discovery
- Network inspection
- Container inspection
- Connectivity probes
- Host metadata
- Docker operations
- Event streaming

The central server becomes the control plane.

---

# 31. Event Architecture

```text
Docker
  |
  v
Docker Events
  |
  v
Agent
  |
  v
Event Bus
  |
  +-- Inventory
  +-- Topology
  +-- Drift
  +-- WebSocket
          |
          v
         UI
```

This enables real-time updates.

---

# 32. Compose Awareness

Discover:

```text
Compose Project
|
+-- frontend
+-- api
+-- worker
+-- postgres
|
+-- networks
    +-- frontend
    +-- backend
```

Compose project and service information should be available in the network topology.

---

# 33. Multi-provider and Multi-host Architecture

```text
                 DockNet
                    |
          +---------+---------+
          |                   |
      Production             Dev
          |                   |
     +----+----+          +---+---+
     |    |    |          |       |
    H1   H2   H3         H4      H5
```

Filters:

- Environment
- Host
- Driver
- Network
- Application
- Owner
- CIDR
- Status

---

# 34. Overlay Support

Overlay networking should be represented with its specific semantics.

Display:

```text
Driver:
overlay

Scope:
swarm

Hosts:
3

Encryption:
enabled

Attachable:
yes
```

Do not treat overlay as equivalent to a local bridge network.

---

# 35. AI Architecture

AI is a later intelligence layer.

```text
                     User
                       |
                       v
                 AI Assistant
                       |
                   LangGraph
                       |
       +---------------+---------------+
       |               |               |
       v               v               v
 Inventory Tool     IPAM Tool      Policy Tool
       |               |               |
       +---------------+---------------+
                       |
                       v
                Analysis Engine
                       |
                       v
                Action Proposal
                       |
                       v
                      HITL
                       |
                 +-----+-----+
                 |           |
              Approve      Reject
                 |
                 v
              Executor
```

---

# 36. AI Use Cases

Examples:

### Inventory

> Show all production networks.

### Troubleshooting

> Why can't frontend connect to postgres?

### Risk

> Can I safely delete old_backend?

### Recommendation

> Suggest a network design for this Compose application.

### Policy

> Why is prod-api non-compliant?

### Drift

> What changed on the production Docker hosts?

### Remediation

> Fix the network drift.

AI must propose destructive actions rather than silently execute them.

---

# 37. LangGraph Agent

Conceptual graph:

```text
START
 |
 v
Understand Request
 |
 v
Gather Infrastructure State
 |
 v
Analyze
 |
 v
Generate Recommendation
 |
 v
Risk Assessment
 |
 v
Human Approval?
 |
 +---- YES ----> Execute ----> Verify ----> Audit ----> END
 |
 +---- NO -------------------------------> END
```

---

# 38. LLM Provider Abstraction

Do not hard-code the product to one model provider.

Interface:

```text
LLM Provider
|
+-- Ollama
+-- OpenAI
+-- Azure OpenAI
+-- AWS Bedrock
+-- Anthropic
```

For local development, Ollama can be the first implementation.

The AI layer should receive structured infrastructure context rather than arbitrary raw Docker output.

---

# 39. Repository Structure

Recommended repository:

```text
network-control-plane/
|
+-- README.md
+-- LICENSE
+-- CONTRIBUTING.md
+-- SECURITY.md
+-- CODE_OF_CONDUCT.md
|
+-- docs/
|   +-- product/
|   |   +-- vision.md
|   |   +-- personas.md
|   |   +-- problem-statement.md
|   |   +-- use-cases.md
|   |   +-- competitive-analysis.md
|   |
|   +-- requirements/
|   |   +-- requirements.md
|   |   +-- functional-requirements.md
|   |   +-- non-functional-requirements.md
|   |
|   +-- architecture/
|   |   +-- architecture.md
|   |   +-- components.md
|   |   +-- data-model.md
|   |   +-- api.md
|   |   +-- security.md
|   |
|   +-- adr/
|   |   +-- ADR-001-backend.md
|   |   +-- ADR-002-database.md
|   |   +-- ADR-003-agent.md
|   |
|   +-- roadmap/
|   |   +-- roadmap.md
|   |   +-- release-plan.md
|   |   +-- feature-intake.md
|   |
|   +-- implementation/
|       +-- tasks.md
|       +-- definition-of-done.md
|       +-- release-gates.md
|       +-- development-workflow.md
|       +-- testing-strategy.md
|
+-- backend/
|   +-- app/
|   |   +-- api/
|   |   +-- core/
|   |   +-- models/
|   |   +-- schemas/
|   |   +-- services/
|   |   +-- docker/
|   |   +-- inventory/
|   |   +-- topology/
|   |   +-- ipam/
|   |   +-- policy/
|   |   +-- drift/
|   |   +-- jobs/
|   |
|   +-- tests/
|
+-- frontend/
|   +-- src/
|       +-- components/
|       +-- pages/
|       +-- features/
|       |   +-- hosts/
|       |   +-- networks/
|       |   +-- containers/
|       |   +-- topology/
|       |   +-- ipam/
|       |   +-- policies/
|       +-- api/
|       +-- stores/
|       +-- types/
|
+-- agent/
|   +-- docknet-agent/
|
+-- ai/
|   +-- graph/
|   +-- tools/
|   +-- prompts/
|   +-- providers/
|
+-- migrations/
|
+-- deployment/
|   +-- docker-compose.yml
|   +-- compose/
|   +-- helm/
|
+-- lab/
|   +-- compose/
|   +-- scripts/
|   +-- scenarios/
|
+-- scripts/
|
+-- tests/
|   +-- integration/
|   +-- e2e/
|
+-- .github/
    +-- workflows/
```

---

# 40. Recommended Development Workflow

The blueprint is the product source of truth.

Do **not** start coding by giving the entire blueprint to a coding assistant and saying:

> "Build DockNet."

Instead use a controlled pipeline:

```text
Blueprint
   |
   v
Requirements
   |
   v
Architecture
   |
   v
MVP Definition
   |
   v
Epics
   |
   v
Tasks
   |
   v
Implementation
   |
   v
Tests
   |
   v
Review
   |
   v
Release Gate
```

---

# 41. Coding Assistant Workflow

Use the coding assistant as an implementation partner, not as the product owner.

## Step 1 — Give it project context

Create:

```text
AGENTS.md
```

or an equivalent coding-assistant instruction file.

It should define:

- Product purpose
- Technology stack
- Repository structure
- Coding standards
- Testing requirements
- Security requirements
- Docker safety rules
- MVP boundaries
- Definition of done
- How requirements/tasks are referenced

---

## Step 2 — Give it one task at a time

Bad:

> Build the backend.

Good:

> Implement P02-003 Network Discovery.

Provide:

- Task ID
- Requirement
- Relevant architecture
- Expected behavior
- API contract
- Tests
- Acceptance criteria

---

## Step 3 — Require a plan before implementation

For each task:

```text
Task
 |
 +-- Understand
 |
 +-- Inspect existing code
 |
 +-- Identify affected components
 |
 +-- Propose implementation
 |
 +-- Implement
 |
 +-- Test
 |
 +-- Review
```

---

## Step 4 — Require tests with implementation

Never:

```text
Implementation -> tests later
```

Prefer:

```text
Requirement
   |
Acceptance Criteria
   |
Tests
   |
Implementation
   |
Validation
```

---

# 42. Recommended Coding Assistant Instruction

Use this principle:

```text
You are an implementation assistant for DockNet Control Plane.

Do not invent product requirements.

Use the repository documentation as the source of truth.

Before changing architecture, identify the relevant ADR.

Implement only the requested task.

Do not silently expand scope.

Do not add Kubernetes, AI, multi-host or unrelated features
unless the active task explicitly requires them.

For every implementation:
1. Inspect existing code.
2. State the implementation approach.
3. Make the smallest appropriate change.
4. Add/update tests.
5. Run relevant tests.
6. Report changed files.
7. Report remaining issues.
```

---

# 43. MVP Strategy — Docker First, Platform Neutral

The MVP should be developed in vertical slices.

Do not build:

```text
all backend
then all frontend
then testing
```

Instead build:

```text
Feature
  |
Backend
  |
API
  |
UI
  |
Docker
  |
Test
  |
Done
```

---

# 44. MVP-0 — Foundation

Goal:

> Establish a clean, testable project.

Deliver:

- Repository
- Documentation
- Backend skeleton
- Frontend skeleton
- PostgreSQL
- Docker Compose
- CI
- Health endpoints
- Basic test framework
- Development standards

Definition of done:

```text
docker compose up

Backend: healthy
Frontend: healthy
Database: healthy
CI: passing
```

---

# 45. MVP-1 — Docker Discovery

Goal:

> See what exists.

Features:

- Connect to one Docker Engine
- Discover networks
- Discover containers
- Store inventory
- Display networks
- Display containers
- Display network membership

Acceptance:

```text
Open DockNet
  |
Connect Docker
  |
See networks
  |
Select network
  |
See attached containers
```

---

# 46. MVP-2 — Network Management

Goal:

> Safely manage Docker networks.

Features:

- Create
- Delete
- Connect
- Disconnect
- Inspect
- Validation
- Preview
- Audit

Acceptance:

```text
Create network from UI
  |
Docker network exists

Connect container
  |
Docker membership changes

Disconnect
  |
Docker membership changes

Delete
  |
Docker network removed
```

---

# 47. MVP-3 — Topology

Goal:

> Understand the infrastructure visually.

Features:

- Network nodes
- Container nodes
- Relationships
- Search
- Filter
- Highlight
- Real-time refresh

Acceptance:

> The topology accurately represents the Docker network/container relationships.

This is the first major **product differentiation milestone**.

---

# 48. MVP-4 — IPAM

Goal:

> Understand and validate network addressing.

Features:

- CIDR
- Gateway
- IP range
- Allocation
- Utilization
- Conflict detection

Acceptance:

```text
Create conflicting network
        |
DockNet detects conflict
        |
Creation blocked or warning shown
```

---

# 49. MVP-5 — Multi-host / Provider Foundation

Goal:

> Manage Docker infrastructure rather than one Docker daemon.

Features:

- Host registration
- Host health
- Host synchronization
- Host grouping
- Environment grouping
- Cross-host inventory
- Cross-host topology

---

# 50. MVP-6 — Governance

Goal:

> Enforce networking standards.

Features:

- Policies
- Compliance
- RBAC
- Audit
- Policy evaluation

---

# 51. MVP-7 — Drift/GitOps

Goal:

> Move from imperative management to controlled desired state.

Features:

- Desired state
- YAML definitions
- State snapshots
- Drift detection
- Plan
- Approval
- Apply
- Verification

---

# 52. MVP-8 — Agentic AI

Goal:

> Add intelligence to the control plane.

Features:

- Natural-language queries
- Diagnostics
- Recommendations
- Risk analysis
- Remediation planning
- HITL approval
- Execution
- Verification
- Audit

---

# 52A. Long-Term Platform Roadmap

The MVP sequence deliberately does **not** attempt to implement every future provider.

```text
Phase A — Docker Foundation
    Single Docker host
        ↓
Phase B — Docker Fleet
    Multiple Docker hosts
        ↓
Phase C — Provider Abstraction
    Formal adapter contracts + normalized domain
        ↓
Phase D — Container Platforms
    Kubernetes / Podman / other runtimes
        ↓
Phase E — Cloud Networking
    AWS / Azure / GCP / private cloud
        ↓
Phase F — Enterprise Networking
    IPAM / firewalls / switches / routing / policy systems
        ↓
Phase G — Intent + AI Operations
    Desired state + autonomous diagnostics + governed remediation
        ↓
Phase H — Enterprise Secrets & Key Vault Integration
    HashiCorp Vault / AWS Secrets Manager / Azure Key Vault / Zero-Trust Secrets Provider
```

### Expansion Gate

A new provider should only be introduced when:

- The core domain model is sufficient
- The adapter contract is stable
- Provider capabilities can be represented explicitly
- Provider-specific behavior remains isolated
- Existing providers pass regression tests
- The addition solves a validated user problem

This prevents premature multi-platform engineering.

# 53. MVP Dependency Map

```text
MVP-0 Foundation
      |
      v
MVP-1 Discovery
      |
      v
MVP-2 Management
      |
      +--------+
      |        |
      v        v
   MVP-3     MVP-4
 Topology    IPAM
      |        |
      +--------+
           |
           v
        MVP-5
      Multi-host
           |
           v
        MVP-6
      Governance
           |
           v
        MVP-7
       Drift
           |
           v
        MVP-8
     Agentic AI
```

---

# 54. MVP-0 Tasks

```text
P00-001 Create repository
P00-002 Create README
P00-003 Create Blueprint.md
P00-004 Create AGENTS.md
P00-005 Create development workflow
P00-006 Create FastAPI skeleton
P00-007 Create React skeleton
P00-008 Configure PostgreSQL
P00-009 Configure Docker Compose
P00-010 Configure CI
P00-011 Configure Pytest
P00-012 Configure frontend tests
P00-013 Create ADR structure
P00-014 Create feature intake process
P00-015 Create definition of done
```

---

# 55. MVP-1 Tasks

```text
P01-001 Docker client abstraction
P01-002 Docker connectivity health check
P01-003 Network discovery
P01-004 Network persistence
P01-005 Container discovery
P01-006 Container persistence
P01-007 Network/container mapping
P01-008 Network API
P01-009 Container API
P01-010 Network list UI
P01-011 Network detail UI
P01-012 Container UI
P01-013 Inventory synchronization
P01-014 Unit tests
P01-015 Integration tests
```

---

# 56. MVP-2 Tasks

```text
P02-001 Create network service
P02-002 Create network API
P02-003 Create network UI
P02-004 Delete safety analysis
P02-005 Delete network API
P02-006 Delete network UI
P02-007 Connect container
P02-008 Disconnect container
P02-009 Operation preview
P02-010 Job model
P02-011 Job execution
P02-012 Audit events
P02-013 Error handling
P02-014 Integration tests
P02-015 E2E tests
```

---

# 57. MVP-3 Tasks

```text
P03-001 Topology data model
P03-002 Graph API
P03-003 React Flow
P03-004 ELK layout
P03-005 Network nodes
P03-006 Container nodes
P03-007 Relationship edges
P03-008 Search
P03-009 Filters
P03-010 Highlight
P03-011 Real-time updates
P03-012 Topology tests
```

---

# 58. MVP-4 Tasks

```text
P04-001 CIDR parser
P04-002 Subnet validation
P04-003 Gateway validation
P04-004 IP allocation calculation
P04-005 Conflict detection
P04-006 Utilization calculation
P04-007 IPAM API
P04-008 IPAM UI
P04-009 Conflict UI
P04-010 IPAM tests
```

---

# 59. MVP-5 Tasks

```text
P05-001 Host model
P05-002 Host registration
P05-003 Host health
P05-004 Host synchronization
P05-005 Agent protocol
P05-006 Agent
P05-007 Multi-host inventory
P05-008 Environment grouping
P05-009 Cross-host topology
P05-010 Multi-host tests
```

---

# 60. MVP-6 Tasks

```text
P06-001 Policy schema
P06-002 Policy engine
P06-003 Driver policies
P06-004 CIDR policies
P06-005 Label policies
P06-006 Naming policies
P06-007 Compliance results
P06-008 Compliance UI
P06-009 RBAC
P06-010 Audit improvements
P06-011 Governance tests
```

---

# 61. MVP-7 Tasks

```text
P07-001 Desired-state schema
P07-002 YAML parser
P07-003 State snapshots
P07-004 State comparison
P07-005 Drift detection
P07-006 Drift UI
P07-007 Remediation plan
P07-008 Approval workflow
P07-009 Apply
P07-010 Verification
P07-011 Git integration
P07-012 Drift tests
```

---

# 62. MVP-8 Tasks

```text
P08-001 LLM abstraction
P08-002 Ollama provider
P08-003 LangGraph setup
P08-004 Inventory tools
P08-005 Topology tools
P08-006 IPAM tools
P08-007 Policy tools
P08-008 Diagnostic agent
P08-009 Recommendation agent
P08-010 Remediation planner
P08-011 HITL
P08-012 AI execution
P08-013 Verification
P08-014 AI audit
P08-015 Agent tests
```

---

# 63. Testing Strategy

Three mandatory levels:

## Unit Tests

Test:

- CIDR validation
- Policy evaluation
- Topology transformation
- Docker response parsing
- Business rules
- Risk analysis

## Integration Tests

Test:

- FastAPI
- PostgreSQL
- Docker Engine
- Docker SDK
- Event processing

## End-to-End Tests

Test:

```text
Browser
  |
API
  |
DockNet
  |
Docker
  |
Network
```

---

# 64. Docker Networking Test Lab

Create:

```text
lab/
|
+-- compose/
|   +-- basic/
|   +-- multi-network/
|   +-- static-ip/
|   +-- isolated/
|   +-- broken/
|
+-- scripts/
|   +-- create-lab.ps1
|   +-- destroy-lab.ps1
|   +-- inject-drift.ps1
|
+-- scenarios/
    +-- subnet-conflict.md
    +-- unreachable-container.md
    +-- orphan-network.md
    +-- policy-violation.md
```

The lab should deliberately create healthy and broken networking scenarios.

---

# 65. Failure Injection Scenarios

Minimum scenarios:

1. Duplicate CIDR
2. Overlapping subnet
3. Orphan network
4. Container attached to wrong network
5. Policy violation
6. Docker host unavailable
7. Agent disconnected
8. Network deleted externally
9. Desired-state drift
10. Invalid gateway
11. Invalid IP range
12. Unauthorized operation

---

# 66. Observability

Use:

- Structured logging
- Prometheus metrics
- OpenTelemetry

Important metrics:

```text
docker_hosts_total
docker_hosts_healthy
networks_total
containers_total
network_operations_total
network_operation_failures
inventory_sync_duration
drift_detected_total
policy_violations_total
```

---

# 67. Security Requirements

Minimum:

- Authentication
- Authorization
- TLS
- Input validation
- Audit
- Docker API isolation
- Secrets management
- Rate limiting
- CSRF protection where applicable

Enterprise:

- OIDC
- LDAP
- RBAC
- Service accounts
- API tokens
- Vault integration

---

# 68. Deployment

## Development

```text
docker compose up
```

Services:

```text
frontend
backend
postgres
redis
```

## Small Production

```text
DockNet API
Frontend
PostgreSQL
Redis
```

## Enterprise

```text
Load Balancer
      |
DockNet API
      |
+-----+------+
|            |
PostgreSQL  Redis
|
DockNet Agents
|
+----+----+----+
H1   H2   H3
```

---

# 69. Release Strategy

## R0 — Foundation

Repository, architecture, CI/CD, development environment.

## R1 — Discovery

Docker host, network and container inventory.

## R2 — Management

Network CRUD and container attachment operations.

## R3 — Topology

Interactive network graph.

## R4 — IPAM

Address management and conflict detection.

## R5 — Multi-host

Centralized Docker infrastructure management.

## R6 — Governance

Policies, compliance and RBAC.

## R7 — Drift/GitOps

Desired state, drift and remediation.

## R8 — Agentic AI

Intelligent troubleshooting and controlled automation.

---

# 70. Definition of Done

Every task must satisfy:

```text
[ ] Code implemented
[ ] Unit tests
[ ] Integration tests where applicable
[ ] E2E tests where applicable
[ ] API documented
[ ] Error handling
[ ] Logging
[ ] Security validation
[ ] Documentation updated
[ ] No scope expansion
[ ] CI passes
```

---

# 71. Release Gates

## R0 Gate

```text
Architecture complete
Repository builds
CI passes
Docker Compose works
```

## R1 Gate

```text
Docker networks discovered
Containers discovered
Relationships displayed
```

## R2 Gate

```text
Networks can be safely modified
Operations audited
```

## R3 Gate

```text
Topology accurately represents Docker state
```

## R4 Gate

```text
IPAM correctly detects subnet conflicts
```

Only proceed when the current gate is satisfied.

---

# 72. Feature Intake Rule

For every new feature:

```text
Feature:
___________

Problem:
___________

User:
___________

Value:
___________

Complexity:
___________

Dependencies:
___________

MVP impact:
___________

Decision:
[ ] MVP
[ ] Current Release
[ ] Future Release
[ ] Reject
```

This prevents uncontrolled scope growth.

---

# 73. Coding Assistant Operating Model

The coding assistant is an implementation partner.

It is **not** the product owner.

The repository documentation is the source of truth.

Recommended flow:

```text
Blueprint
    |
    v
Requirements
    |
    v
Architecture
    |
    v
MVP
    |
    v
Epic
    |
    v
Task
    |
    v
Coding Assistant
    |
    +-- Inspect
    +-- Plan
    +-- Implement
    +-- Test
    +-- Review
    |
    v
Human Review
    |
    v
Task Complete
```

---

# 74. AGENTS.md / Coding Rules

Create `AGENTS.md` in the repository root.

It should contain:

```text
You are an implementation assistant for DockNet Control Plane.

The repository documentation is the source of truth.

Do not invent product requirements.

Before changing architecture, identify the relevant ADR.

Implement only the requested task.

Do not silently expand scope.

Do not add Kubernetes, AI, multi-host or unrelated functionality
unless explicitly required by the current task.

Before implementation:
1. Inspect the repository.
2. Inspect relevant documentation.
3. Identify affected components.
4. State the implementation approach.

During implementation:
1. Make the smallest appropriate change.
2. Follow existing patterns.
3. Add/update tests.
4. Avoid unrelated refactoring.

After implementation:
1. Run relevant tests.
2. Run lint/type checks.
3. Report changed files.
4. Report test results.
5. Report remaining issues.
6. Identify documentation that needs updating.
```

---

# 75. Task-Based Coding Prompt

Each coding session should look approximately like:

```text
Task ID: P01-003

Task:
Implement Docker network discovery.

Read:
- docs/requirements/requirements.md
- docs/architecture/components.md
- docs/architecture/data-model.md

Requirements:
- Connect to Docker Engine.
- Retrieve networks.
- Normalize Docker response.
- Persist network inventory.
- Handle Docker API errors.

Acceptance Criteria:
1. Network list is returned.
2. Network attributes are persisted.
3. Duplicate synchronization does not create duplicates.
4. Docker connection errors are handled.
5. Unit tests exist.
6. Integration test exists.

Constraints:
- Do not implement container discovery.
- Do not implement topology.
- Do not modify unrelated modules.

First inspect the repository and propose the implementation.
```

This is much more reliable than asking the coding assistant to implement large phases in one shot.

---

# 76. Development Loop

For every feature:

```text
1. Read requirement
       |
2. Identify acceptance criteria
       |
3. Inspect code
       |
4. Write/confirm tests
       |
5. Implement
       |
6. Run tests
       |
7. Review diff
       |
8. Update documentation
       |
9. Commit
       |
10. Close task
```

---

# 77. Git Strategy

Recommended:

```text
main
 |
 +-- develop
       |
       +-- feature/P01-003-network-discovery
       +-- feature/P01-004-network-persistence
       +-- feature/P02-001-create-network
```

Commit examples:

```text
feat(network): add Docker network discovery

test(network): add discovery integration tests

fix(network): handle Docker connection timeout

docs(network): document discovery API
```

---

# 78. MVP Completion Rule

A phase is complete only when:

```text
Requirements
    |
    v
Implementation
    |
    v
Tests
    |
    v
Documentation
    |
    v
Acceptance Criteria
    |
    v
Release Gate
    |
    v
DONE
```

Do not continue adding features indefinitely to an MVP.

---

# 79. Recommended First Build

The first coding milestone should be:

## Network Control Plane v0.1-alpha

Scope:

```text
Single Docker Host

+-- Docker connection
+-- Network discovery
+-- Container discovery
+-- Network/container relationships
+-- Network list
+-- Network detail
+-- Network creation
+-- Network deletion
+-- Container connect
+-- Container disconnect
+-- Basic audit
+-- Basic topology
```

Do **not** start with:

```text
AI
Kubernetes
Multi-host
GitOps
Advanced policy
Enterprise SSO
```

---

# 80. The First Vertical Slice

The first meaningful feature should be:

> **Discover and display Docker networks.**

End-to-end:

```text
Docker Engine
      |
Docker SDK
      |
Backend Service
      |
FastAPI
      |
React API Client
      |
Network List
      |
Network Detail
```

Then extend the same slice:

```text
Discovery
   |
Management
   |
Topology
   |
IPAM
```

---

# 81. Long-Term Product Architecture

Final vision:

```text
                    +--------------------------+
                    |   DockNet Control Plane  |
                    +------------+-------------+
                                 |
          +----------------------+----------------------+
          |                      |                      |
          v                      v                      v
     DISCOVERY              TOPOLOGY                 IPAM
          |                      |                      |
          +----------------------+----------------------+
                                 |
                                 v
                           MANAGEMENT
                                 |
                                 v
                           GOVERNANCE
                                 |
                     +-----------+-----------+
                     |                       |
                     v                       v
                   POLICY                  AUDIT
                     |
                     v
                    DRIFT
                     |
                     v
                   GITOPS
                     |
                     v
                    HITL
                     |
                     v
                AGENTIC AI
                     |
          +----------+----------+
          |          |          |
          v          v          v
       Diagnose  Recommend  Remediate
```

---

# 82. Final Product Definition

> **The Network Control Plane is an open-source control plane for modern application and workload networking. It provides unified discovery, topology, IPAM, policy, governance, drift detection, desired-state reconciliation and safe automation across heterogeneous infrastructure. Docker is the first supported provider, while the core architecture remains provider-neutral and is designed to expand toward Kubernetes, cloud and enterprise networking.**

## Product Positioning in One Sentence

> **A control plane that turns fragmented workload networking into one observable, governable and automatable system.**

## What Makes This Defensible

The long-term differentiation should not be the ability to create a Docker network.

It should be the combination of:

1. Normalized cross-provider network intelligence
2. Network topology and relationship reasoning
3. IPAM and conflict intelligence
4. Policy and governance
5. Desired-state and drift reconciliation
6. Safe operational workflows
7. Provider adapters
8. Human-in-the-loop automation
9. Agentic AI grounded in deterministic infrastructure tools
10. Full auditability and explainability

Docker is therefore the **wedge**, not the **moat**.

# 82A. Naming Recommendation

### Recommended decision for now

Use:

> **Network Control Plane**

as the product category and neutral working title.

Do **not** force a permanent brand decision before the architecture and MVP validate the problem.

Once MVP-3/MVP-4 demonstrates product-market signal, select a distinctive brand through:

- Trademark search
- Domain availability
- GitHub organization/repository availability
- PyPI/npm/package availability
- Social handle availability
- Search-engine collision analysis
- International pronunciation and meaning checks

The final brand should communicate **network intelligence, control, connectivity, orchestration or infrastructure**, without naming a specific runtime or cloud.

# 83. Immediate Next Steps

Do these in order:

```text
1. Create GitHub repo using the neutral repository name `network-control-plane`sitory
        |
2. Add Blueprint.md
        |
3. Add AGENTS.md
        |
4. Create docs/ structure
        |
5. Extract MVP-0 requirements
        |
6. Create architecture.md
        |
7. Create tasks.md
        |
8. Create Docker development environment
        |
9. Implement P00-001 onward
        |
10. Do not move to MVP-1 until R0 gate passes
```

The **Blueprint.md is the product-level source of truth**.

The repository's detailed documents should be derived from it, and implementation tasks should be derived from those documents.

This prevents the common failure mode:

```text
Idea
  |
  v
Code
  |
  v
More ideas
  |
  v
More code
  |
  v
Lost roadmap
  |
  v
Never finished
```

The intended model is:

```text
VISION
  |
REQUIREMENTS
  |
ARCHITECTURE
  |
MVP
  |
TASKS
  |
CODE
  |
TEST
  |
RELEASE
  |
NEXT MVP
```
