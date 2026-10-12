# Problem Statement & Product Justification — Network Control Plane

**Product Name:** Network Control Plane  
**Tagline:** Visualize. Manage. Validate. Govern. Automate Workload Networking.  
**Authoritative References:** `Blueprint.md`, `Requirements.md`, `Architecture.md`  

---

## 1. Executive Summary

As container adoption scales from single developer workstations to multi-host container fleets, Docker Swarm clusters, and hybrid edge environments, **container networking has emerged as the single most prone vector for operational outages, silent IP collisions, and visibility blind spots**.

Existing tooling forces engineering teams to choose between **shallow UI wrappers** (which execute destructive CLI calls blindly) and **heavy Kubernetes CNI infrastructure** (which require complex clusters and lack deterministic safety validation).

The **Network Control Plane** addresses this fundamental gap by introducing a **provider-neutral, safety-first network control plane**. It combines live multi-host inventory discovery, interactive topology graph visualizers, deterministic pre-flight safety risk evaluation engines, built-in IP Address Management (IPAM), and immutable audit logging.

---

## 2. The Core Problem Statement

Modern containerized operations face four structural pain points:

### 💥 Pain Point 1: Unprotected Mutating Operations & Outage Vulnerability
In standard container management tools, deleting a network or detaching a container endpoint is treated as a simple database CRUD operation. Operators can delete a network currently serving active production database containers or shared API gateways with a single click. **There is zero pre-flight risk analysis** to warn the operator about impacted container workloads, active microservice dependencies, or Docker Compose project references before execution.

### 🔍 Pain Point 2: Black-Box Network Topology & Blind Spot Inspection
Network engineers and developers inspect container networking by sifting through complex raw JSON arrays output by CLI commands (`docker network inspect <id>`, `docker inspect <container>`). Existing dashboards render simple text tables listing network names, but fail to render interactive, multi-layer topology graphs that visually map how workload container nodes connect across virtual networks, subnets, and host gateways.

### ⚡ Pain Point 3: Silent IPAM Conflicts & Subnet Overlaps
As container environments expand across multiple hosts, teams frequently encounter silent CIDR subnet overlaps (e.g. Host A allocating `172.18.0.0/16` while Host B allocates `172.18.5.0/24`) or duplicate static IP assignments. Standard container runtimes do not proactively detect these overlaps, causing runtime network packet drops, routing failures, and container startup crashes that are notoriously difficult to debug.

### 📜 Pain Point 4: Absence of Operations Auditability & Governance
In multi-tenant environments or team workflows, mutating actions (network creation, endpoint detachment, pruning) occur without centralized audit logging. Incident responders cannot determine *who* modified a network configuration, *when* an endpoint was disconnected, or *what* safety risk level was evaluated prior to execution.

---

## 3. Comparative Matrix: Network Control Plane vs. Existing Tools

| Architectural Feature | Docker Desktop / CLI | Portainer | NetBox / Nautobot | Cilium / Weave Scope | **Network Control Plane** |
|---|---|---|---|---|---|
| **Primary Focus** | Single-host developer runtime | General container CRUD UI | Enterprise DCIM/IPAM Spreadsheet | Kubernetes eBPF CNI / Dataplane | **Dedicated Workload Network Control Plane** |
| **Pre-Flight Safety Risk Engine** | ❌ None | ❌ None | ❌ None | ❌ None | **✅ Built-in Risk Calculator (LOW/MED/HIGH/CRITICAL)** |
| **Interactive Topology Visualizer** | ❌ None | ❌ None | ❌ None | ⚠️ Heavy packet graph (requires K8s) | **✅ Native React Flow & ELK Graph Visualizer** |
| **IPAM Subnet Overlap Detection** | ❌ None | ❌ None | ⚠️ Manual spreadsheet entries | ❌ None | **✅ Automated Real-Time CIDR Conflict Engine** |
| **Immutable Operational Audit Log** | ❌ None | ⚠️ Basic activity log | ⚠️ DB audit trail | ❌ None | **✅ Dedicated Immutable Operations Audit Event Log** |
| **Provider Neutrality** | ❌ Locked to Docker | ⚠️ Docker/K8s wrapper | N/A (Static DB) | ❌ Locked to Linux CNI/eBPF | **✅ Provider-Neutral Adapter Architecture (A1)** |
| **Read-Before-Write Execution** | ❌ Direct mutation | ❌ Direct mutation | N/A | N/A | **✅ Discover → Validate → Risk Analysis → Approve → Audit** |

---

## 4. Key Differentiators: Why Network Control Plane is Needed

### 1. Safety-First Mutation Policy (Invariant A3)
Unlike Portainer or Docker Desktop, the Network Control Plane enforces a strict **Read-Before-Write** pipeline:
```text
Discover -> Validate -> Risk Analysis / Preview -> User Approval -> Execute -> Verify -> Audit Event
```
Before any network deletion or container detachment command reaches the underlying Docker engine socket, the **Pre-Deletion Safety Analysis Engine** calculates an explicit risk rating (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), identifies all impacted workloads, checks Compose project labels, and blocks unsafe actions unless explicitly overridden by an operator.

### 2. Built-in IPAM Conflict Engine Without Infrastructure Bloat
NetBox requires manual human entry and updating. Cilium requires a multi-node Kubernetes cluster with custom Linux kernels. Network Control Plane automatically discovers live Docker IPAM configurations, computes CIDR subnet utilization percentages (`allocated / usable %`), and proactively alerts operators to overlapping CIDR ranges across hosts *before* deployment failures happen.

### 3. Native Interactive Graph Topology
Rather than requiring third-party packet sniffing daemons, Network Control Plane generates real-time, event-driven node/edge topology graphs using `@xyflow/react` and `@dagrejs/dagre`. Engineers can instantly visualize host-to-network and container-to-network edge connections with live status indicators.

### 4. Zero Vendor Lock-in & Extensible Provider Adapters
Built upon strict **Provider Neutrality (Invariant A1)**, core domain models never import provider SDKs. The capability interface supports Docker Engine today and easily extends to Docker Swarm, Kubernetes CNI adapters, and cloud VPCs without changing core UI or policy logic.

---

## 5. Conclusion & Value Proposition

The **Network Control Plane** fills the missing layer between basic container UI dashboards and heavy enterprise service meshes. It empowers DevOps engineers, System Administrators, and Network Architects with **complete visual clarity, automated IPAM governance, and non-disruptive, audit-backed operations safety**.
