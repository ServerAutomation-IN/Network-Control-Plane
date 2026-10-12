# Proposal IMP-03: One-Click Host Onboarding Wizard & Automated Bootstrap Script

**Status:** ✅ IMPLEMENTED  
**Target Component:** `frontend/src/features/topology/`, `backend/app/api/v1/hosts.py`, `scripts/`  
**Priority:** High  
**Estimated Effort:** Medium (2 days)  

---

## 1. Problem Statement
Currently, onboarding a remote host requires:
1. Manually finding or configuring an API key.
2. Manually creating a python virtual environment on the target host.
3. Installing the agent wheel via `pip`.
4. Writing a custom `systemd` service unit or starting `main.py` in the background.

This creates friction for operations teams who manage tens or hundreds of edge nodes and virtual machines.

---

## 2. Proposed Solution: One-Liner Onboarding Experience

Add a **"+ Connect Host"** button in the Network Control Plane web UI:

```text
+-----------------------------------------------------------------------+
|  🖥️ Connect Infrastructure Host                                     |
+-----------------------------------------------------------------------+
|  Choose Host OS / Environment:                                        |
|  [ Linux (x86_64 / ARM64) ]   [ Windows Server ]   [ Docker Desktop ] |
|                                                                       |
|  Run this command on your host terminal:                              |
|  +-----------------------------------------------------------------+  |
|  | curl -sSL https://ncp.corp/install.sh | sudo bash -s --        |  |
|  |   --control-plane https://ncp.corp                              |  |
|  |   --token ncp_boot_9f81a7b8e2194c6d                             |  |
|  +-----------------------------------------------------------------+  |
|  [ Copy Command ]                                                     |
|                                                                       |
|  Waiting for host heartbeat... ⏳                                     |
+-----------------------------------------------------------------------+
```

---

## 3. Architecture & Security Flow

```mermaid
sequenceDiagram
    autonumber
    actor Admin as Platform Admin
    participant UI as NCP Web UI
    participant API as NCP Backend API
    participant Host as Target Host Machine

    Admin->>UI: Clicks "+ Connect Host"
    UI->>API: POST /api/v1/hosts/bootstrap-token
    API-->>UI: Returns { token: "ncp_boot_...", expires_in: 900 }
    Admin->>Host: Pastes one-liner curl bash command
    Host->>API: GET /install.sh
    Host->>API: POST /api/v1/agent/enroll (with bootstrap token)
    API->>API: Validate token, generate persistent Agent API Key & Host ID
    API-->>Host: Returns { host_id, persistent_api_key }
    Host->>Host: Creates /etc/systemd/system/network-control-plane-agent.service
    Host->>Host: systemctl enable --now network-control-plane-agent
    Host->>API: First POST /api/v1/agent/snapshot
    API-->>UI: Realtime WebSocket notice: Host 'node-01' Connected!
```

### Security Guardrails:
* **Ephemeral Tokens:** Bootstrap tokens expire in 15 minutes and can only be used once.
* **Role Enforcement:** Only users with `admin` role can issue bootstrap tokens.
* **Audit Trail:** Every token creation and successful host enrollment creates an `AuditEvent`.
