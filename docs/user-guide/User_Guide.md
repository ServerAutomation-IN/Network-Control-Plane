# Network Control Plane — Comprehensive User Guide

**Document Version:** 1.0.0-GA  
**Product:** Network Control Plane  
**Target Audience:** Platform Engineers, DevOps Engineers, Cloud Architects, Network & Security Administrators  

---

## 📖 Table of Contents

- [1. Deploying Network-Control-Plane](#1-deploying-network-control-plane)
  - [1.1 System Architecture & Prerequisites](#11-system-architecture--prerequisites)
  - [1.2 Launching the Stack with Docker Compose](#12-launching-the-stack-with-docker-compose)
  - [1.3 Service Verification & Readiness Healthchecks](#13-service-verification--readiness-healthchecks)
- [2. Login and Setup Administrator Account](#2-login-and-setup-administrator-account)
  - [2.1 First-Time Platform Initialization (Setup Modal)](#21-first-time-platform-initialization-setup-modal)
  - [2.2 Standard Username & Password Authentication](#22-standard-username--password-authentication)
  - [2.3 Fast-Track Demo Roles (Sandbox Login)](#23-fast-track-demo-roles-sandbox-login)
- [3. Topology Visualizer](#3-topology-visualizer)
  - [3.1 Canvas Navigation, Auto-Layout & Interactive Controls](#31-canvas-navigation-auto-layout--interactive-controls)
  - [3.2 Dynamic Search & Multi-Host Filtering](#32-dynamic-search--multi-host-filtering)
  - [3.3 Deep Node & Link Inspection Drawer](#33-deep-node--link-inspection-drawer)
  - [3.4 Real-Time Streaming Updates (SSE & WebSockets)](#34-real-time-streaming-updates-sse--websockets)
- [4. Network & Workloads](#4-network--workloads)
  - [4.1 Create Network](#41-create-network)
  - [4.2 Inspect](#42-inspect)
  - [4.3 Delete](#43-delete)
- [5. IPAM & Subnets](#5-ipam--subnets)
  - [5.1 IPAM & Conflicts](#51-ipam--conflicts)
  - [5.2 Subnet Pools & Utilization Map](#52-subnet-pools--utilization-map)
  - [5.3 Subnet & Static IP Allocation Validator](#53-subnet--static-ip-allocation-validator)
- [6. Policy & Compliance](#6-policy--compliance)
  - [6.1 Policy Governance & Compliance Dashboard](#61-policy-governance--compliance-dashboard)
  - [6.2 Evaluate All Policies](#62-evaluate-all-policies)
  - [6.3 Create Policy](#63-create-policy)
  - [6.4 Active Policy Definitions](#64-active-policy-definitions)
  - [6.5 Compliance Violations](#65-compliance-violations)
- [7. GitOps & Drift](#7-gitops--drift)
  - [7.1 Desired-State, Drift Detection & GitOps Dashboard](#71-desired-state-drift-detection--gitops-dashboard)
  - [7.2 Declare Specs & Plan](#72-declare-specs--plan)
  - [7.3 GitOps Auto-Sync Repositories (Compare Desired VS Actual)](#73-gitops-auto-sync-repositories-compare-desired-vs-actual)
  - [7.4 Declarative Desired-State Manifest (YAML) with Git Sync](#74-declarative-desired-state-manifest-yaml-with-git-sync)
  - [7.5 Reconciliation Plan & Approval Gate](#75-reconciliation-plan--approval-gate)
- [8. Immutable Audit Logs](#8-immutable-audit-logs)
  - [8.1 Immutable Compliance Audit Log & Ledger; SHA-256 Tamper-Proof; export Audit Trail CSV](#81-immutable-compliance-audit-log--ledger-sha-256-tamper-proof-export-audit-trail-csv)
  - [8.2 Risk level, actor, Hiding routine system ingest](#82-risk-level-actor-hiding-routine-system-ingest)
- [9. Settings and Integration](#9-settings-and-integration)
  - [9.1 Cloud & Hypervisors (Hyper-V, VMware, Nutanix, AWS, Azure, GCP)](#91-cloud--hypervisors-hyper-v-vmware-nutanix-aws-azure-gcp)
  - [9.2 LLM Connection Panel (Ollama, OpenAI, Azure OpenAI, Anthropic)](#92-llm-connection-panel-ollama-openai-azure-openai-anthropic)
  - [9.3 SSO Authentication (Keycloak, Okta, Microsoft Entra ID)](#93-sso-authentication-keycloak-okta-microsoft-entra-id)
  - [9.4 Users & Role Governance](#94-users--role-governance)
  - [9.5 Webhook Channels](#95-webhook-channels)
  - [9.6 Execution Queue](#96-execution-queue)
  - [9.7 Key Vault & Secrets Management (HashiCorp Vault, AWS Secrets Manager, Azure Key Vault, Local Fernet)](#97-key-vault--secrets-management-hashicorp-vault-aws-secrets-manager-azure-key-vault-local-fernet)
- [10. Governed Network AI Assistant](#10-governed-network-ai-assistant)
  - [10.1 AI Assistant Drawer](#101-ai-assistant-drawer)
  - [10.2 Natural Language Topology Queries](#102-natural-language-topology-queries)
  - [10.3 Reachability & Diagnostic Analysis](#103-reachability--diagnostic-analysis)
  - [10.4 Plan & Remediation Proposals (Human-in-the-Loop)](#104-plan--remediation-proposals-human-in-the-loop)

---

## 1. Deploying Network-Control-Plane

### 1.1 System Architecture & Prerequisites
**Network Control Plane** runs as an enterprise-grade, containerized multi-tier stack designed for zero-overhead local homelab exploration and scalable production deployment:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                      STACK ARCHITECTURE OVERVIEW                       │
├─────────────────────┬──────────────┬───────────────────────────────────┤
│ Component           │ Port Binding │ Technical Function                │
├─────────────────────┼──────────────┼───────────────────────────────────┤
│ Web UI Dashboard    │ 3001         │ React 18, Vite, React Flow        │
│ FastAPI Backend     │ 8000         │ Python 3.12, Pydantic v2, SSE     │
│ PostgreSQL Store    │ 5432         │ PostgreSQL 16 (Async SQLAlchemy)  │
│ Redis & Worker      │ 6379         │ Redis 7 + ARQ Task Queue          │
│ Host Agent (Local)  │ Unix / Named │ Bi-directional daemon collector   │
└─────────────────────┴──────────────┴───────────────────────────────────┘
```

**Minimum Prerequisites:**
- **OS:** Linux (Ubuntu 22.04+, RHEL 9+), macOS (Apple Silicon or Intel), or Windows 10/11 with WSL2.
- **Runtimes:** Docker Engine 24.0+ and Docker Compose v2.20+.
- **Resources:** Minimum 2 vCPUs and 4 GB RAM (8 GB recommended for multi-host fleets).

### 1.2 Launching the Stack with Docker Compose
To deploy the complete platform locally:

```bash
# 1. Clone the repository
git clone https://github.com/ServerAutomation-IN/Network-Control-Plane.git
cd Network-Control-Plane

# 2. Prepare environment variables
cp deployment/.env.example deployment/.env

# 3. Spin up all services in detached mode
docker compose -f deployment/docker-compose.yml up -d
```

### 1.3 Service Verification & Readiness Healthchecks
Verify that all services are running and healthy:

```bash
docker compose -f deployment/docker-compose.yml ps
```

Expected output:
```text
NAME                     IMAGE                      STATUS                  PORTS
network-backend          network-control-plane-api  Up (healthy)            0.0.0.0:8000->8000/tcp
network-frontend         network-control-plane-web  Up (healthy)            0.0.0.0:3001->3001/tcp
network-postgres         postgres:16-alpine         Up (healthy)            0.0.0.0:5432->5432/tcp
network-redis            redis:7-alpine             Up (healthy)            0.0.0.0:6379->6379/tcp
```

**Service Endpoints:**
- **Web User Interface:** `http://localhost:3001`
- **Backend Health Check:** `http://localhost:8000/health` (Returns `{"status": "healthy"}`)
- **Swagger / OpenAPI Documentation:** `http://localhost:8000/docs`

> [!NOTE]
> *Next Step:* Once the containers are healthy, proceed to **Chapter 2** to initialize your root administrator credentials.

---

## 2. Login and Setup Administrator Account

### 2.1 First-Time Platform Initialization (Setup Modal)
When accessing `http://localhost:3001` on a freshly deployed instance, the platform detects that no administrator account exists and automatically presents the **First-Time Administrator Setup Modal**:

```text
┌────────────────────────────────────────────────────────────────────────┐
│ 🛡️ FIRST-TIME PLATFORM INITIALIZATION                                   │
├────────────────────────────────────────────────────────────────────────┤
│ No administrator account found. Initialize root credentials to begin.  │
│                                                                        │
│ Username:         [ admin                            ]                 │
│ Email Address:    [ admin@network-control-plane.local]                 │
│ Master Password:  [ ••••••••••••••••                 ]                 │
│ Confirm Password: [ ••••••••••••••••                 ]                 │
│                                                                        │
│ [ Initialize & Sign In ]                                               │
└────────────────────────────────────────────────────────────────────────┘
```

1. Enter your chosen **Username** (default: `admin`).
2. Enter an administrative **Email Address**.
3. Choose a strong **Master Password** (minimum 8 characters).
4. Click **Initialize & Sign In**. The system securely hashes the password with bcrypt, stores the root administrator record, and redirects you directly to the **Topology Visualizer**.

### 2.2 Standard Username & Password Authentication
For subsequent logins:
1. Navigate to `http://localhost:3001/login`.
2. Under the **Credentials** tab, enter your registered **Username** and **Password**.
3. Click **Sign In**. A cryptographically signed JWT token is issued and stored in your secure session cookie.

### 2.3 Fast-Track Demo Roles (Sandbox Login)
For lab evaluations, staging walkthroughs, and role validation, quick demo role buttons are available at the bottom of the login screen:
- 👑 **Admin:** Full read/write governance, policy editing, GitOps reconciliation, and system settings.
- ⚡ **Operator:** Operational privileges to create, inspect, and delete low-risk networks, and trigger GitOps syncs.
- 👁️ **Viewer:** Read-only access to topology graphs, IPAM maps, and audit logs.

> [!NOTE]
> *Next Step:* With your administrator session authenticated, proceed to **Chapter 3** to explore the real-time topology map.

---

## 3. Topology Visualizer

### 3.1 Canvas Navigation, Auto-Layout & Interactive Controls
The **Topology Visualizer** is the primary situational awareness cockpit. Powered by **React Flow** and the **ELK.js** hierarchical layout engine, it displays all physical hosts, virtual bridges, overlay networks, and connected containers:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        CANVAS NAVIGATION CONTROLS                      │
├─────────────────────┬──────────────────────────────────────────────────┤
│ Control Action      │ Mouse / Keyboard Shortcut                        │
├─────────────────────┼──────────────────────────────────────────────────┤
│ Zoom In / Zoom Out  │ Mouse Scroll Wheel or [+] / [-] buttons          │
│ Pan Canvas          │ Click and Drag any blank canvas space            │
│ Select / Focus Node │ Left-click on any Host, Network, or Container    │
│ Recenter Graph      │ Click the [🎯 Fit View] button                   │
│ Recompute Layout    │ Click the [⚡ Auto-Layout] button                 │
└─────────────────────┴──────────────────────────────────────────────────┘
```

### 3.2 Dynamic Search & Multi-Host Filtering
Filter large environments containing hundreds of containers:
- **Search Bar:** Type any subnet CIDR (e.g., `10.240.`), container name (e.g., `redis-cache`), or network name. Matching nodes are highlighted in amber while unrelated elements fade.
- **Driver Filter Dropdown:** Isolate networks by driver type (`bridge`, `overlay`, `macvlan`, `ipvlan`, `host`).
- **Host Filter Dropdown:** Toggle between `All Hosts`, the local engine (`local-docker-engine`), or remote Linux/Windows/Cloud agents enrolled via Settings.

### 3.3 Deep Node & Link Inspection Drawer
Clicking any canvas node slides open the **Topology Inspector Drawer** on the right side of the screen:
- **Network Node:** Inspects subnet range, gateway IP, driver, scope, internal status, and all connected container endpoints.
- **Container Node:** Shows assigned IPv4/IPv6 addresses, MAC addresses, connection state, published ports, and container runtime ID.
- **Host Node:** Displays host OS, architecture, engine version, total container count, and agent heartbeat latency.

### 3.4 Real-Time Streaming Updates (SSE & WebSockets)
The topology canvas maintains a live connection to `/api/v1/events/stream` via Server-Sent Events (SSE). When containers start, stop, attach, or detach on any connected host:
- The graph automatically updates without requiring a page reload.
- New edge connections pulse smoothly into place.
- Removed workloads animate gracefully out of view.

> [!NOTE]
> *Next Step:* From visualizing current state, proceed to **Chapter 4** to manage networks and workloads.

---

## 4. Network & Workloads

### 4.1 Create Network
Create virtual bridges, overlay meshes, or isolated internal subnets through the declarative creation modal:

```text
┌────────────────────────────────────────────────────────────────────────┐
│ ➕ CREATE NETWORK WIZARD                                               │
├────────────────────────────────────────────────────────────────────────┤
│ Host:             [ local-docker-engine                    ▼ ]         │
│ Network Name:     [ prod-payments-net                        ]         │
│ Driver:           (o) Bridge   ( ) Overlay   ( ) Macvlan   ( ) IPvlan  │
│ Subnet CIDR:      [ 10.150.20.0/24                           ]         │
│ Gateway IP:       [ 10.150.20.1                              ]         │
│ Options:          [X] Internal Network (No External Internet)          │
│                   [ ] Attachable (Allow ad-hoc containers)             │
│ Labels:           [ env=prod, tier=backend, pci=true         ]         │
│                                                                        │
│ [ Cancel ]                                         [ Create Network ]  │
└────────────────────────────────────────────────────────────────────────┘
```

**Step-by-Step Instructions:**
1. Navigate to **Networks & Workloads** from the left navigation bar.
2. Click the **+ Create Network** button in the upper right.
3. Select the **Target Host** where the network will be provisioned.
4. Provide a unique **Network Name** (e.g., `prod-payments-net`).
5. Choose the **Driver** (`bridge`, `overlay`, `macvlan`, or `ipvlan`).
6. Specify the **Subnet CIDR** (e.g., `10.150.20.0/24`) and **Gateway IP** (e.g., `10.150.20.1`). The built-in IPAM engine verifies in real-time that no CIDR collisions exist.
7. Toggle **Internal Network** `ON` if workloads must not route to the public internet.
8. Click **Create Network**. The control plane dispatches the operation to the host agent and records an immutable audit event.

### 4.2 Inspect
To inspect a network and its attached workloads:
1. In the **Networks & Workloads** table, click on any network row.
2. The detailed drawer displays:
   - **Network ID & Scope:** Driver, scope (`local` or `global`), and creation timestamp.
   - **Subnet Configuration:** Usable IP capacity, allocated addresses, and gateway.
   - **Attached Workloads:** List of connected containers, assigned IP addresses, and MAC addresses.
3. **Attach Container:** Click **Attach Workload**, select an unattached container from the dropdown, optionally specify a static IP, and confirm.

### 4.3 Delete
Deleting a network requires strict validation to prevent accidental outages under **Invariant A3 (Read Before Write & Safety Analysis)**:

```text
┌────────────────────────────────────────────────────────────────────────┐
│ ⚠️ PRE-FLIGHT BLAST-RADIUS RISK EVALUATION                             │
├────────────────────────────────────────────────────────────────────────┤
│ Target Network:  prod-db-net (Driver: bridge, Host: host-01)           │
│ Calculated Risk: 🔴 HIGH RISK (Score: 85/100)                          │
│                                                                        │
│ Impact Analysis:                                                       │
│ • 2 Active Workloads Attached: ['postgres-primary', 'pgpool-lb']       │
│ • Dependent Docker Compose Project Detected: 'ecommerce-stack'         │
│                                                                        │
│ 🛑 SAFEGUARD: Network deletion blocked while workloads are attached.   │
│ Please detach containers before deleting this network.                 │
└────────────────────────────────────────────────────────────────────────┘
```

**Risk Classification Tiers:**
- 🟢 **`LOW` (0–25):** Empty network with zero attached containers. Safe to delete immediately.
- 🟡 **`MEDIUM` (26–50):** Contains stopped or dormant workloads. Requires explicit operator confirmation.
- 🟠 **`HIGH` (51–75):** Active running containers attached. Deletion is blocked until containers are detached.
- 🔴 **`CRITICAL` (76–100):** System default bridge (`bridge`, `host`, `none`) or cross-host overlay gateway. Deletion is permanently disabled.

> [!NOTE]
> *Next Step:* To manage subnet capacity and prevent address overlap, proceed to **Chapter 5**.

---

## 5. IPAM & Subnets

### 5.1 IPAM & Conflicts
The **IP Address Management (IPAM)** engine provides global visibility across all Docker, Podman, and Cloud subnets:
- **Global Subnet Registry:** Tracks all CIDR blocks across all managed hosts.
- **CIDR Overlap Detector:** Continuously cross-references subnets to flag overlapping address blocks (e.g., `172.20.0.0/16` vs. `172.20.5.0/24`) and conflicting gateway allocations.
- **Conflict Badging:** Subnets with detected collisions are flagged with a red ⚠️ **CONFLICT** badge in both the IPAM table and the Topology Visualizer.

### 5.2 Subnet Pools & Utilization Map
Navigate to **IPAM & Subnets** to view the live capacity map:

```text
┌────────────────────────────────────────────────────────────────────────┐
│ 📊 SUBNET CAPACITY & UTILIZATION MAP                                   │
├──────────────────────┬─────────────┬──────────────┬────────────────────┤
│ Subnet CIDR          │ Host        │ Allocated/Cap│ Utilization Visual │
├──────────────────────┼─────────────┼──────────────┼────────────────────┤
│ 172.17.0.0/16        │ local-docker│ 4 / 65534    │ █░░░░░░░░░░  0.01% │
│ 10.240.10.0/24       │ host-agent-1│ 210 / 254    │ ████████░░  82.68% │
│ 192.168.100.0/24     │ host-agent-2│ 245 / 254    │ █████████░  96.46% │
└──────────────────────┴─────────────┴──────────────┴────────────────────┘
```

**Utilization Thresholds:**
- 🟢 **Normal (`<70%`):** Healthy capacity.
- 🟡 **Warning (`70%–85%`):** Nearing saturation; consider subnet expansion.
- 🔴 **Critical (`>85%`):** Address exhaustion imminent; new container allocations may fail.

### 5.3 Subnet & Static IP Allocation Validator
Before provisioning a new network or assigning a static IP to a container, use the **Dry-Run Allocation Validator**:
1. Scroll to the **Allocation Validator** card on the IPAM page.
2. Enter the proposed **Subnet CIDR** (e.g., `10.200.4.0/24`).
3. Optionally enter a proposed **Static IP** (e.g., `10.200.4.15`).
4. Click **Validate Allocation**.
5. The engine executes a pre-flight evaluation and returns:
   - ✅ `VALID`: Subnet is available; static IP falls within assignable pool boundaries and does not collide with existing endpoints.
   - ❌ `CONFLICT`: Displays exact conflicting network ID and overlapping CIDR range.

> [!NOTE]
> *Next Step:* With IP addresses allocated safely, proceed to **Chapter 6** to enforce organizational guardrails via Policy & Compliance.

---

## 6. Policy & Compliance

### 6.1 Policy Governance & Compliance Dashboard
Navigate to **Policy & Compliance** to review your organization's security posture and compliance score:
- **Fleet Compliance Score:** Percentage metric (e.g., `92% Compliance`) summarizing all active policy evaluations across all networks.
- **Active Policies Count:** Number of rules currently enabled and enforced.
- **Violations Counter:** Tally of non-compliant network configurations categorized by severity (`ERROR`, `WARNING`, `INFO`).

### 6.2 Evaluate All Policies
To execute an on-demand audit across your entire infrastructure:
1. Click the **Evaluate All Policies** button in the dashboard header.
2. The control plane inspects every network, bridge, and workload against active policy definitions in milliseconds.
3. The compliance gauge and violations table update immediately with fresh findings.

### 6.3 Create Policy
Click **+ Create Policy** to define a new declarative governance rule:

```text
┌────────────────────────────────────────────────────────────────────────┐
│ 📜 CREATE COMPLIANCE POLICY                                            │
├────────────────────────────────────────────────────────────────────────┤
│ Policy Name:  [ enforce-private-rfc1918-cidrs                        ] │
│ Description:  [ Prevent creation of public IP ranges on bridge nets  ] │
│ Rule Type:    ( ) DRIVER_WHITELIST      (o) CIDR_RESTRICTION           │
│               ( ) MANDATORY_LABELS      ( ) ISOLATION_ENFORCEMENT      │
│ Target CIDRs: [ 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16            ] │
│ Severity:     ( ) INFO       ( ) WARNING       (o) ERROR (Block)       │
│                                                                        │
│ [ Cancel ]                                           [ Save Policy ]   │
└────────────────────────────────────────────────────────────────────────┘
```

**Supported Rule Types:**
- **`DRIVER_WHITELIST`:** Restricts network creation to approved drivers (e.g., only `overlay` and `bridge`).
- **`CIDR_RESTRICTION`:** Mandates that all subnets fall within approved private IP ranges (RFC 1918).
- **`MANDATORY_LABELS`:** Requires specific metadata tags (e.g., `env`, `owner`, `cost-center`) on every network.
- **`ISOLATION_ENFORCEMENT`:** Mandates that production networks must have the `Internal` flag enabled to prevent internet routing.

### 6.4 Active Policy Definitions
The **Active Policy Definitions** card displays all configured rules:
- **Toggle Switch:** Instantly enable or disable any policy without deleting its definition.
- **Severity Badge:** Visual indicator (`ERROR`, `WARNING`, `INFO`). Rules marked `ERROR` automatically block non-compliant creations in the [Create Network Wizard](#41-create-network).

### 6.5 Compliance Violations
When a network violates an active policy:
- The violation appears in the **Compliance Violations** table with the **Violating Network Name**, **Host**, **Severity**, and **Failure Reason**.
- Click **Inspect Resource** to jump directly to the offending network, view attached workloads, and apply corrective remediation.

> [!NOTE]
> *Next Step:* To manage configurations declaratively through version control, proceed to **Chapter 7** for GitOps & Drift reconciliation.

---

## 7. GitOps & Drift

### 7.1 Desired-State, Drift Detection & GitOps Dashboard
Navigate to **GitOps & State Sync** to manage declarative infrastructure as code:
- **Repository Sync Status:** Shows `SYNCED`, `DRIFT_DETECTED`, or `SYNCING`.
- **Commit Details:** Displays the active commit hash, branch, and author.
- **Auto-Sync Toggle:** Enables scheduled background polling (e.g., every 5 minutes) to automatically detect drift.

### 7.2 Declare Specs & Plan
Under GitOps governance, network definitions are authored in version-controlled Git repositories. The control plane fetches these declarations, computes the runtime delta, and generates an execution plan before any mutations occur.

### 7.3 GitOps Auto-Sync Repositories (Compare Desired VS Actual)
To connect a Git repository:
1. Click **+ Add Repository**.
2. Configure repository details:
   - **Repository URL:** HTTPS Git clone URL (e.g., `https://github.com/my-org/network-specs.git`).
   - **Branch:** Target branch (e.g., `main` or `production`).
   - **Manifest Path:** Directory containing YAML manifests (e.g., `deploy/networks/`).
   - **Credentials URI:** Optional secret reference from Key Vault (e.g., `vault://secret/git#token`).
3. Click **Connect & Sync**. The system clones the repository, parses the manifests, and compares desired state against the runtime environment.

### 7.4 Declarative Desired-State Manifest (YAML) with Git Sync
Network specifications use the clean `network-control-plane/v1` declarative syntax:

```yaml
apiVersion: network-control-plane/v1
kind: NetworkSpec
metadata:
  name: prod-payments-net
  environment: production
  host: local-docker-engine
spec:
  driver: bridge
  internal: true
  attachable: false
  ipam:
    subnet: 10.240.50.0/24
    gateway: 10.240.50.1
  labels:
    tier: backend
    compliance: pci-dss
    managed-by: gitops
```

### 7.5 Reconciliation Plan & Approval Gate
When runtime state diverges from the Git manifest:

```text
┌────────────────────────────────────────────────────────────────────────┐
│ 🔄 RECONCILIATION PLAN (DRIFT DETECTED)                                │
├────────────────────────────────────────────────────────────────────────┤
│ Proposed Actions:                                                      │
│  + CREATE Network: 'prod-payments-net' (Driver: bridge, 10.240.50.0/24)│
│  ~ UPDATE Network: 'prod-analytics' (Add Label: 'tier=backend')        │
│  - DELETE Network: 'temp-debug-net' (Unmanaged / Orphaned)             │
│                                                                        │
│ 🛡️ APPROVAL GATE: Manual operator approval required for execution.   │
│                                                                        │
│ [ Reject Plan ]                                   [ Approve & Apply ]  │
└────────────────────────────────────────────────────────────────────────┘
```

1. Click **View Drift Diff** to inspect proposed additions (`+`), modifications (`~`), and removals (`-`).
2. Verify that the reconciliation actions match your operational intent.
3. Click **Approve & Apply**. The background ARQ queue safely executes the corrective mutations and logs an immutable `AuditEvent`.

> [!NOTE]
> *Next Step:* Every action taken in GitOps, Network creation, and Policy evaluation is recorded in **Chapter 8: Immutable Audit Logs**.

---

## 8. Immutable Audit Logs

### 8.1 Immutable Compliance Audit Log & Ledger; SHA-256 Tamper-Proof; export Audit Trail CSV
Navigate to **Audit Logs** to view the tamper-proof compliance ledger:
- **Append-Only Ledger:** Every mutating request, authentication attempt, GitOps sync, and policy evaluation generates an append-only `AuditEvent`.
- **Cryptographic Fingerprint:** Each record includes a SHA-256 hash computed over the timestamp, actor, action, resource ID, and request payload. Any manual tampering with the database breaks the hash chain and triggers an alert.
- **Export Audit Trail (CSV):** Click the **📥 Export Audit Trail (CSV)** button in the header to download a complete compliance record for SOC2 Type II, ISO 27001, or HIPAA auditors.

### 8.2 Risk level, actor, Hiding routine system ingest
Filter the audit table to focus on critical security events:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        AUDIT LEDGER FILTER BAR                         │
├────────────────────────────────────────────────────────────────────────┤
│ Filter by Actor:     [ ALL    ]  [ HUMAN  ]  [ SYSTEM ]                │
│ Risk Classification: [ ALL    ]  [ CRITICAL ]  [ HIGH ]  [ MEDIUM ]    │
│ Routine Ingest:      [X] Hide Routine System Ingest (Agent Snapshots)  │
└────────────────────────────────────────────────────────────────────────┘
```

- **Filter by Actor:** Switch between `HUMAN` (actions taken by operators in the UI or API) and `SYSTEM` (automated background tasks).
- **Risk Level:** Filter by severity (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`).
- **Hide Routine System Ingest:** Toggle `ON` (default) to filter out high-frequency agent inventory heartbeat snapshots (`AGENT_SNAPSHOT_INGEST`), keeping the view focused on actionable administrative mutations.

> [!NOTE]
> *Next Step:* To configure platform integrations, cloud providers, LLMs, and secrets, proceed to **Chapter 9: Settings and Integration**.

---

## 9. Settings and Integration

### 9.1 Cloud & Hypervisors (Hyper-V, VMware, Nutanix, AWS, Azure, GCP)
Navigate to **Settings & Integrations** -> **Cloud & Hypervisors** to connect external compute runtimes:
- **Microsoft Hyper-V / SCVMM:** Connect to Hyper-V hosts or Virtual Machine Manager endpoints to inspect virtual switches (`vSwitch`) and private VM networks.
- **VMware vSphere & NSX-T:** Connect to VMware vCenter to discover distributed virtual switches (DVS), port groups, and NSX-T overlay segments.
- **Nutanix AHV:** Integrate with Nutanix Prism Element / Prism Central to track Acropolis Hypervisor (AHV) virtual networks.
- **AWS Cloud VPC:** Ingest AWS VPCs, subnets, route tables, and security groups via IAM credentials.
- **Azure Virtual Network:** Sync Azure VNets, subnets, and Network Security Groups (NSGs).
- **GCP Cloud VPC:** Discover Google Cloud Compute VPC networks and subnetwork IP allocations.

### 9.2 LLM Connection Panel (Ollama, OpenAI, Azure OpenAI, Anthropic)
Navigate to **Settings & Integrations** -> **LLM Connection Settings Panel** to configure your organization's AI diagnostic model provider:

```text
┌────────────────────────────────────────────────────────────────────────┐
│ 🤖 LLM CONNECTION CONTROL PANEL                                        │
├────────────────────────────────────────────────────────────────────────┤
│ Provider Selection:                                                    │
│  ( ) Ollama (Local)      (o) OpenAI          ( ) Azure OpenAI          │
│  ( ) Anthropic Claude                                                  │
│                                                                        │
│ Endpoint URL: [ https://api.openai.com/v1                            ] │
│ Model Name:   [ gpt-4o                                               ] │
│ API Key:      [ •••••••••••••••••••••••••••••••••••••••••••••••••••• ] │
│                                                                        │
│ [ Test LLM Connection ]                              [ Save Settings ] │
└────────────────────────────────────────────────────────────────────────┘
```

- **🦙 Ollama (Local):** Local private inference with zero external cloud dependencies (`http://localhost:11434`, models: `qwen2.5-coder:7b`, `llama3.3`, `deepseek-r1`).
- **🟢 OpenAI:** Cloud API endpoint (`https://api.openai.com/v1`, models: `gpt-4o`, `o3-mini`, `gpt-4o-mini`).
- **🔷 Azure OpenAI:** Managed enterprise deployment (`https://your-resource.openai.azure.com/`, deployment ID: `gpt-4o-deployment`).
- **🟧 Anthropic:** Claude API (`https://api.anthropic.com/v1`, models: `claude-3-7-sonnet-20250219`, `claude-3-5-sonnet`).

> [!TIP]
> Click **Test LLM Connection** to run an automated diagnostic ping before saving your settings.

### 9.3 SSO Authentication (Keycloak, Okta, Microsoft Entra ID)
Navigate to **Settings & Integrations** -> **SSO & Authentication**:
- **Keycloak OIDC:** Standard OpenID Connect discovery URL (`https://auth.example.com/realms/corp/.well-known/openid-configuration`), Client ID, and Client Secret.
- **Okta SSO:** Enterprise SAML 2.0 / OIDC application configuration with automatic group-to-role attribute mapping. (See [Okta SSO Configuration Guide](Okta_SSO_Configuration_Guide.md) for full setup instructions).
- **Microsoft Entra ID (Azure AD):** Azure AD OAuth2 tenant integration for Single Sign-On.

### 9.4 Users & Role Governance
Navigate to **Settings & Integrations** -> **User Management**:
- **Onboard User:** Enter new user's username, email, initial password, and assigned role.
- **Role Permissions:**
  - `Administrator`: Full access to mutate networks, configure SSO, manage secrets, and onboard users.
  - `Operator`: Create, delete (low risk), and attach networks; approve GitOps reconciliation plans.
  - `Viewer`: Read-only access to topology diagrams, IPAM pools, and audit logs.

### 9.5 Webhook Channels
Navigate to **Settings & Integrations** -> **Outbound Webhooks**:
1. Click **+ Register Webhook Channel**.
2. Configure:
   - **Channel Name:** E.g., `slack-ops-alerts` or `datadog-events`.
   - **Payload URL:** HTTPS target endpoint.
   - **HMAC Secret Key:** Shared secret string used to compute the `X-Signature-256` payload verification signature.
   - **Subscribed Events:** Select triggers (`network.created`, `network.deleted`, `security.drift`, `compliance.violation`).
3. Click **Test & Register Channel**.

### 9.6 Execution Queue
Navigate to **Settings & Integrations** -> **Task Queue**:
Monitor and trigger asynchronous operations managed by the Redis/ARQ engine:
- **Enqueue GitOps Sync Task:** Forces an immediate background pull and drift calculation across all connected Git repositories.
- **Enqueue Unmanaged Sweep:** Scans for orphaned or unattached bridge networks across hosts.
- **Refresh Queue:** Real-time metrics on queued, active, and completed task jobs.

### 9.7 Key Vault & Secrets Management (HashiCorp Vault, AWS Secrets Manager, Azure Key Vault, Local Fernet)
Navigate to **Settings & Integrations** -> **Key Vault & Secrets**:
Configure dynamic secret URI resolution (`vault://`, `aws-secret://`, `azure-vault://`) so production credentials are never stored in plaintext:
- **HashiCorp Vault:** Vault server URL (`http://vault.internal:8200`), KV mount path (`secret/`), and Vault Token.
- **AWS Secrets Manager:** AWS region and access credentials.
- **Azure Key Vault:** Key Vault URI (`https://myvault.vault.azure.net/`) and Service Principal credentials.
- **Local Fernet AES-256:** Built-in symmetric encryption key for air-gapped and local homelab deployments.

> [!NOTE]
> *Next Step:* With integrations and models configured, proceed to **Chapter 10** to interact with the Governed Network AI Assistant.

---

## 10. Governed Network AI Assistant

### 10.1 AI Assistant Drawer
The **Governed Network AI Assistant** provides human-supervised, diagnostic reasoning for complex network topologies:
- **Open Drawer:** Click the **✨ AI Diagnostic Assistant** button in the top navigation bar or press `Ctrl + /` from any screen.
- **Persistent Context:** The drawer maintains awareness of the currently selected host, network, or container on your canvas.
- **Model Status:** Shows the active LLM provider (Ollama, OpenAI, Azure OpenAI, or Anthropic) configured in Settings.

### 10.2 Natural Language Topology Queries
Ask questions in plain English to quickly query complex infrastructure state:
- *"Show all bridge networks with more than 50% IP capacity used"*
- *"Which containers are connected to the internal database network?"*
- *"Are there any CIDR conflicts between our Docker hosts and AWS VPCs?"*
- *"List all networks created manually outside of GitOps version control."*

### 10.3 Reachability & Diagnostic Analysis
When two workloads fail to communicate:
1. Select or input the **Source Container** and **Target Container**.
2. Click **Diagnose Reachability**.
3. The diagnostic engine performs a deterministic topology traversal:
   - Analyzes shared bridge and overlay networks.
   - Detects network isolation failures and gateway mismatches.
   - Evaluates MTU discrepancies and route path connectivity.
   - Pinpoints the exact hop where traffic is dropped.

### 10.4 Plan & Remediation Proposals (Human-in-the-Loop)
In strict adherence to **Invariant A5 (Deterministic First & Safety Gate)**:
- The AI assistant **cannot** directly mutate infrastructure.
- If reachability is broken, it formulates a structured **Remediation Proposal Card**:

```text
┌────────────────────────────────────────────────────────────────────────┐
│ 🛠️ AI REMEDIATION PROPOSAL                                            │
├────────────────────────────────────────────────────────────────────────┤
│ Diagnosis:                                                             │
│ Workload 'payment-api' cannot reach 'order-db' because they reside on │
│ isolated bridge networks on 'host-01'.                                 │
│                                                                        │
│ Proposed Remediation:                                                  │
│ Attach workload 'payment-api' to network 'prod-payments-net'           │
│                                                                        │
│ Blast-Radius Risk: 🟢 LOW RISK (0 workloads impacted)                 │
│                                                                        │
│ [ Reject Proposal ]                            [ Approve & Execute ]   │
└────────────────────────────────────────────────────────────────────────┘
```

- An authorized Operator or Administrator must review the proposed action and click **Approve & Execute** to apply the fix, ensuring total operational safety.

---

## 📚 Related Documentation

- **[System Architecture Specification](../architecture/Architecture.md)** — Architectural invariants (A1–A4), adapter isolation, and data flows.
- **[Deployment & Configuration Guide](../deployment/Deployment_and_Configuration_Guide.md)** — Comprehensive Administrator guide covering high availability, database maintenance, and security hardening.
- **[Okta SSO Configuration Guide](Okta_SSO_Configuration_Guide.md)** — Step-by-step administrator guide for Okta OIDC SSO integration and role mapping.
- **[Product Blueprint](../product/Blueprint.md)** — Core domain models, capability specifications, and architectural invariants.
