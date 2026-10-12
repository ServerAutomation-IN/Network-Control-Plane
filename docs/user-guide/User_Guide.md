# Network Control Plane — User Guide

**Document Version:** 1.0.0-GA  
**Product:** Network Control Plane  
**Target Audience:** Platform Engineers, DevOps Engineers, Network Administrators, System Operators  

---

## 1. Product Overview & Core Navigation

The **Network Control Plane** web interface empowers engineering teams to visualize, manage, validate, and govern workload networking across multi-host container clusters and cloud VPCs.

### Navigation Dashboard Layout
When logging into the platform at `http://localhost:3000`, the top navigation bar gives access to the 7 core feature modules:

1. **📊 Executive Dashboard:** Real-time summary of active hosts, networks, subnets, attached containers, and system alerts.
2. **🌐 Networks & Workloads:** Tabular list of discovered infrastructure networks, container attachments, and creation/deletion modals.
3. **🗺️ Interactive Topology:** React Flow powered graphical canvas displaying live container-to-network connectivity.
4. **🔢 IPAM & Subnets:** Subnet allocation density, utilization gauges, and IP overlap/conflict warning detector.
5. **🛡️ Policy & Governance:** Compliance dashboard evaluating declarative network policies and RBAC roles.
6. **🔄 GitOps & State Sync:** Desired-state Git repository sync, real-time drift detector, and execution queue monitor.
7. **⚙️ Settings & Integrations:** SSO setup, outbound webhook log viewer, and Key Vault & Secrets Engine manager.

---

## 2. Network Lifecycle Management & Creation Wizard

### Creating a New Network

1. Navigate to **Networks & Workloads** and click the **+ Create Network** button.
2. Fill out the creation form:
   - **Network Name:** Unique string identifier (e.g., `prod-payments-net`).
   - **Driver:** Select network driver (`bridge`, `overlay`, `macvlan`, `ipvlan`).
   - **IPv4 Subnet:** CIDR notation (e.g., `10.240.10.0/24`).
   - **Gateway:** Subnet gateway IP (e.g., `10.240.10.1`).
   - **IP Range (Optional):** Dynamic allocation pool (e.g., `10.240.10.128/25`).
   - **Internal Network:** Toggle to restrict external internet access.
   - **Attachable:** Toggle to allow standalone containers to join overlay networks.
   - **Labels:** Key-value pairs for governance tagging (`env=production`, `owner=fintech`).
3. Click **Preview & Create**. The safety engine verifies CIDR availability before executing network creation.

---

## 3. Safe Network Deletion & Pre-Execution Safety Risk Analysis

To prevent operational outages, mutating actions perform a pre-execution risk analysis.

### Deleting a Network

1. Locate the network in the **Network List** and click **Delete Network**.
2. The **Safety Risk Analysis Modal** evaluates attached workloads and displays a **Risk Score**:

```text
┌────────────────────────────────────────────────────────────────────────┐
│ ⚠️ SAFETY RISK ANALYSIS RESULT                                          │
├────────────────────────────────────────────────────────────────────────┤
│ Risk Score: HIGH RISK (Score: 85/100)                                  │
│ Target Network: prod-backend-net                                       │
│                                                                        │
│ Impact Analysis:                                                       │
│ • 3 Running Containers Attached (payment-api, auth-db, redis-cache)    │
│ • Docker Compose Project Reference Detected: 'docker-compose.yml'       │
│ • Critical Service Dependency Flagged                                  │
│                                                                        │
│ 🛑 ACTION BLOCKED: Detach containers before deleting this network.     │
└────────────────────────────────────────────────────────────────────────┘
```

3. **Risk Categories:**
   - **`LOW`:** Unused/orphaned network. Immediate deletion safe.
   - **`MEDIUM`:** Stopped containers associated. Confirmation required.
   - **`HIGH` / `CRITICAL`:** Active running containers or Compose dependencies attached. Action blocked until endpoints are safely detached.

---

## 4. Interactive Topology Canvas Navigation

The **Interactive Topology Canvas** visualizes complex workload connectivity graphs in real time.

### Canvas Controls & Shortcuts
- **Zoom & Pan:** Scroll mouse wheel to zoom in/out; click and drag canvas to pan.
- **Auto-Layout Button:** Re-align graph using the **ELK.js** layered graph layout engine.
- **Node Highlight:** Click any container node to highlight connected network edges and dim unrelated nodes.
- **Side Panel Inspection:** Select any node to open the inspector drawer detailing IP allocations, MAC addresses, container uptime, and underlying host metrics.
- **Live Event Updates:** Container start/stop and network creation events stream over WebSockets / SSE to instantly update the graph without refreshing the page.

---

## 5. IP Address Management (IPAM) & Conflict Resolution

The **IPAM Dashboard** provides visibility into subnet utilization and addressing conflicts.

### Key Metrics & Indicators
- **Subnet Utilization Gauge:** Displays percentage of allocated IPs (`Allocated IPs / Total Usable Host IPs`).
- **Capacity Warnings:** Subnets exceeding 85% capacity trigger a visual **Yellow/Red Warning**.
- **Conflict Warning Detector:** Automatically scans and flags:
  - **Overlapping Subnets:** Two networks claiming intersecting CIDR blocks (e.g., `172.18.0.0/16` vs `172.18.4.0/24`).
  - **Gateway Mismatches:** Network gateway configured outside subnet boundaries.
  - **Duplicate Static IP Assignments:** Two containers assigned identical IP addresses.

---

## 6. Governance, Policy Engine & RBAC Roles

### Policy Rules Evaluation
The Policy Engine continuously checks active infrastructure against declarative governance rules.

#### Example Policy Checks:
- `RULE-01`: Prohibit unencrypted overlay drivers in Production.
- `RULE-02`: Require `env` and `team` labels on all custom networks.
- `RULE-03`: Restrict subnets to enterprise RFC 1918 private address ranges (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`).

### User Roles & Permissions Matrix

| Platform Feature | Viewer | Operator | Administrator |
|---|---|---|---|
| View Networks & Topology | ✅ | ✅ | ✅ |
| View IPAM & Policy Dashboard | ✅ | ✅ | ✅ |
| Create / Attach Network | ❌ | ✅ | ✅ |
| Prune Unused Networks | ❌ | ✅ | ✅ |
| Delete Network | ❌ | ⚠️ (Low Risk) | ✅ |
| Configure SSO & Webhooks | ❌ | ❌ | ✅ |
| Manage Key Vault Integration | ❌ | ❌ | ✅ |

---

## 7. GitOps Desired-State Automation Workflow

The **GitOps Engine** reconciles declarative YAML state specifications against runtime infrastructure.

### GitOps Workflow Steps

1. **Connect Git Repository:** In **GitOps & State Sync**, provide repository URL (`https://github.com/org/network-specs.git`) and branch (`main`).
2. **Declarative State Format (`network-control-plane/v1`):**
   ```yaml
   apiVersion: network-control-plane/v1
   kind: NetworkSpec
   metadata:
     name: prod-analytics-net
     environment: production
   spec:
     driver: bridge
     ipam:
       subnet: 10.200.5.0/24
       gateway: 10.200.5.1
     labels:
       team: analytics
   ```
3. **Drift Detection:** The engine continuously compares runtime state to Git state. If an operator manually modifies or deletes a network outside Git, a **State Drift Alert** is triggered.
4. **Remediation Plan Approval:** Click **View Drift Plan** to review proposed changes, then click **Approve & Sync** to execute background reconciliation via the Celery task queue.

---

## 8. Enterprise Integrations (SSO, Webhooks & Secrets Vault)

### Setting Up Enterprise Key Vaults

1. Navigate to **Settings & Integrations** -> **🔑 Key Vault & Secrets Engine**.
2. Choose your secret provider: **HashiCorp Vault**, **AWS Secrets Manager**, or **Azure Key Vault**.
3. Input connection credentials or secret URI references:
   - Example Vault URI reference: `vault://secret/data/db#password`
4. Click **Test Key Vault Connection** to run a live diagnostic ping check.

### Outbound Webhook Integration
Receive instant event payloads whenever networks are mutated or policy violations occur:
- **Supported Event Triggers:** `network.created`, `network.deleted`, `container.attached`, `security.drift`, `audit.event`.
- **HMAC Signature Verification:** Webhook headers include `X-Signature-256` computed with your shared secret to ensure payload authenticity.
