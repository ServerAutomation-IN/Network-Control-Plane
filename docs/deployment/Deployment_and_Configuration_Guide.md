# Network Control Plane — Deployment and Configuration Guide (Admin Guide)

**Document Version:** 1.0.0-GA  
**Product:** Network Control Plane  
**Target Audience:** Systems Administrators, DevOps Engineers, Site Reliability Engineers (SREs), Security Officers  

---

## 1. System Requirements & Prerequisites

### Minimum Hardware Specifications

| Component | Small Office / Lab Deployment | Enterprise High-Availability Cluster |
|---|---|---|
| **CPU** | 2 vCPUs (x86_64 / ARM64) | 4+ vCPUs per node |
| **RAM** | 4 GB | 16 GB+ |
| **Storage** | 20 GB SSD | 100 GB+ High-IOPS NVMe |
| **Network** | 1 Gbps NIC | 10 Gbps redundant NICs |

### Software Prerequisites
- **Operating System:** Linux (Ubuntu 22.04 LTS+, RHEL 9+, Debian 12+), macOS 13+, Windows Server 2022 / Windows 11 WSL2.
- **Container Runtime:** Docker Engine 24.0+ and Docker Compose v2.20+.
- **Database:** PostgreSQL 16+ (or managed PostgreSQL like AWS RDS / Azure Database for PostgreSQL).
- **In-Memory Store:** Redis 7.0+ (used for Celery async task queue and caching).
- **Python Runtime:** Python 3.12+ (if running backend natively without Docker).
- **Node.js Runtime:** Node.js 18+ (if building frontend bundle natively).

---

## 2. Deployment Scenarios

### Scenario A: Single-Node Docker Compose (Default / Development)

The single-node Docker Compose setup launches the entire stack (FastAPI backend, React frontend, PostgreSQL 16, and Redis 7) on a single host.

1. Clone the repository and navigate to the deployment directory:
   ```bash
   git clone https://github.com/ServerAutomation-IN/Network-Control-Plane.git
   cd Network-Control-Plane/deployment
   ```

2. Copy the environment template and set strict file permissions:
   ```bash
   # Copy template
   cp .env.example .env

   # Linux / macOS: Restrict to owner only
   chmod 600 .env

   # Windows (PowerShell): Restrict ACL to current user only
   icacls .env /inheritance:r /grant:r "$($env:USERNAME):(R,W)"
   ```
   Edit `.env` to configure your passwords, keys, and identity provider details.

3. Launch containers in background mode:
   ```bash
   docker compose -f docker-compose.yml up -d
   ```

4. Verify service health:
   ```bash
   docker compose ps
   curl -f http://localhost:8000/health
   ```

---

### Scenario B: Multi-Node Production High-Availability (HA) Topology

In enterprise production environments, run stateless application containers separately from managed infrastructure databases:

```text
                        ┌───────────────────────────────┐
                        │      Enterprise TLS / WAF     │
                        │    (NGINX / HAProxy / Traefik)│
                        └───────────────┬───────────────┘
                                        │ HTTPS / WSS
                                        ▼
                  ┌───────────────────────────────────────────┐
                  │    App Nodes (Behind Load Balancer)       │
                  │  ┌─────────────────┐ ┌─────────────────┐  │
                  │  │ Backend Node 1  │ │ Backend Node 2  │  │
                  │  └─────────────────┘ └─────────────────┘  │
                  └─────────────┬───────────┬─────────────────┘
                                │           │
            ┌───────────────────┴───┐   ┌───┴───────────────────┐
            ▼                       ▼   ▼                       ▼
┌───────────────────────┐ ┌───────────────────┐ ┌───────────────────┐
│ Primary PostgreSQL 16 │ │ Redis Cluster 7   │ │ Enterprise Key    │
│ (Managed RDS / Cloud) │ │(Celery Task Broker│ │ Vault (HashiCorp) │
└───────────────────────┘ └───────────────────┘ └───────────────────┘
```

#### Step 1: Database Migration Execution
Apply database schema migrations to external PostgreSQL:
```bash
export DATABASE_URL="postgresql+asyncpg://app_user:strong_password@db-cluster.internal:5432/network_control_plane"
cd backend
alembic upgrade head
```

#### Step 2: Launch Backend Workers & Celery Queue
Start ASGI web server and Celery background queue workers:
```bash
# Start FastAPI Web API
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Start Celery Worker Process
celery -A app.tasks.celery_app worker --loglevel=info --concurrency=8
```

---

### Scenario C: Kubernetes Deployment via Helm

Deploy to Kubernetes using the official Helm chart located in `deployment/helm/`:

```bash
# Add Helm chart directory
cd deployment/helm/network-control-plane

# Customize values.yaml with secrets reference
helm install control-plane . \
  --namespace network-system \
  --create-namespace \
  --set global.postgresql.host="postgres.network-system.svc.cluster.local" \
  --set global.vault.address="https://vault.internal:8200"
```

---

## 3. Comprehensive Environment Variable Directory

| Environment Variable | Description | Required | Default / Example |
|---|---|---|---|
| `DATABASE_URL` | SQLAlchemy Async PostgreSQL connection URI | Yes | `postgresql+asyncpg://postgres:pass@localhost:5432/ncp` |
| `REDIS_URL` | Redis URI for Celery task queue & caching | Yes | `redis://localhost:6379/0` |
| `SECRET_KEY` | 32-byte secret key for local Fernet encryption & JWT tokens | Yes | `e.g. 4f9d2a8c1e3b...` |
| `OKTA_ISSUER_URL` | Okta OIDC Authorization Server URL | No | `https://dev-12345.okta.com/oauth2/default` |
| `OKTA_CLIENT_ID` | Okta Application Client ID | No | `0oa1a2b3c4d5e6f7g8h9` |
| `OKTA_CLIENT_SECRET` | Okta Application Client Secret (Plaintext or Key Vault URI) | No | `vault://secret/data/sso#client_secret` |
| `OKTA_ROLE_CLAIM` | ID Token / Userinfo claim for role mappings | No | `roles` |
| `VAULT_ADDR` | HashiCorp Vault URL | No | `http://127.0.0.1:8200` |
| `VAULT_TOKEN` | HashiCorp Vault authentication token | No | `hvs.xxxxx...` |
| `AWS_REGION` | AWS region for AWS Secrets Manager & AWS VPC adapter | No | `us-east-1` |
| `AZURE_KEYVAULT_URL` | Azure Key Vault URI | No | `https://myvault.vault.azure.net/` |
| `GITOPS_REPO_URL` | Git Repository URL containing state definitions | No | `https://github.com/org/net-specs.git` |
| `GITOPS_SYNC_INTERVAL` | Background Git sync frequency in seconds | No | `300` |
| `LOG_LEVEL` | Application logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) | No | `INFO` |

---

## 4. Security Hardening & Zero-Trust Best Practices

### 4.1 Production Secrets Management & Permissions Hardening Playbook

> [!CAUTION]
> **Strict Security Invariant:**
> Never commit `.env` files, database passwords, or provider API keys into Git repositories or hardcode them in `docker-compose.yml`.

To deploy Network Control Plane with maximum security posture, implement the **Three-Tier Secrets Hierarchy**:

#### Tier 1 (Recommended for Standalone Docker Compose / Staging): `.env` Interpolation + OS File ACL Hardening
1. Keep `docker-compose.yml` clean by using environment variable substitution (`${VAR_NAME}`).
2. Copy the configuration template:
   ```bash
   cp deployment/.env.example deployment/.env
   ```
3. Set exclusive filesystem read/write permissions to protect credentials against unauthorized local accounts:
   - **Linux / macOS:**
     ```bash
     chmod 600 deployment/.env
     ```
   - **Windows (PowerShell):**
     *(POSIX `chmod` is not available on native Windows. Use `icacls` to remove inherited ACLs and grant exclusive read/write access to the current user)*
     ```powershell
     icacls deployment\.env /inheritance:r /grant:r "$($env:USERNAME):(R,W)"
     ```

#### Tier 2 (Recommended for Swarm & Orchestrated Containers): Native Docker / Podman Secrets
Docker Secrets mount credentials as temporary in-memory files located at `/run/secrets/`, preventing credential leakage via `docker inspect` or environment inspection:
```yaml
services:
  backend:
    secrets:
      - db_password
      - okta_client_secret
    environment:
      - POSTGRES_PASSWORD_FILE=/run/secrets/db_password
      - OKTA_CLIENT_SECRET_FILE=/run/secrets/okta_client_secret

secrets:
  db_password:
    file: ./secrets/db_password.txt
  okta_client_secret:
    file: ./secrets/okta_client_secret.txt
```

#### Tier 3 (Enterprise Zero-Trust): Dynamic Key Vault Secret URI Resolution
Eliminate static secrets on host disks entirely by leveraging Network Control Plane's native **Key Vault Resolver**:
- Set credentials in `.env` or deployment specifications as dynamic URIs:
  ```bash
  OKTA_CLIENT_SECRET=vault://secret/data/sso#client_secret
  DATABASE_PASSWORD=aws-secret://prod/db#password
  AGENT_API_TOKEN=azure-vault://ncp-agent-token
  ```
- The backend resolves and decrypts secrets in-memory at boot or on-demand via authenticated TLS connections to HashiCorp Vault, AWS Secrets Manager, or Azure Key Vault.

---

### 4.2 Platform Network & Socket Isolation
1. **API Socket Isolation:** The frontend client MUST NEVER mount or communicate directly with `/var/run/docker.sock`. All provider requests must route through FastAPI backend authentication, RBAC, policy checking, and safety validation.
2. **Reverse Proxy & TLS Termination:** Always enforce TLS 1.3 in front of the control plane API using NGINX, Traefik, or AWS ALB:
   ```nginx
   server {
       listen 443 ssl http2;
       server_name controlplane.example.com;
       ssl_certificate /etc/letsencrypt/live/controlplane/fullchain.pem;
       ssl_certificate_key /etc/letsencrypt/live/controlplane/privkey.pem;

       location / {
           proxy_pass http://localhost:3000;
       }
       location /api/ {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-Proto https;
       }
   }
   ```
3. **Zero Static Credentials:** Configure hypervisor, cloud, and SSO credentials using Key Vault URIs (`vault://`, `aws-secret://`, `azure-vault://`) so sensitive database passwords, tokens, and credentials are dynamically fetched at runtime rather than stored in plain text.

---

## 5. Maintenance, Backup & Recovery

### PostgreSQL Database Backup & Restore

#### Perform Full Database Dump:
```bash
docker exec -t network-control-plane-postgres pg_dump -U postgres -d network_control_plane > ncp_backup_$(date +%Y%m%d).sql
```

#### Restore Database Dump:
```bash
cat ncp_backup_20261007.sql | docker exec -i network-control-plane-postgres psql -U postgres -d network_control_plane
```

### Applying Schema Migrations
Always verify Alembic migrations before launching updated backend binaries:
```bash
docker exec -it network-control-plane-backend alembic upgrade head
```

---

## 6. Monitoring, Telemetry & Diagnostics

- **OpenAPI Documentation:** Access interactive Swagger UI at `http://<host>:8000/docs`.
- **Prometheus Telemetry:** Metric scraping endpoint exposed at `http://<host>:8000/metrics`.
- **Health Checks:**
  - Liveness endpoint: `GET /health`
  - Readiness endpoint: `GET /api/v1/system/readiness`
  - Key Vault diagnostic test: `POST /api/v1/secrets/test`

---

## 7. Troubleshooting Playbook

### Problem 1: Backend returns 500 Error connecting to Docker Daemon
- **Root Cause:** Insufficient permissions on `/var/run/docker.sock`.
- **Remediation:** Grant the backend container process access to the docker group:
  ```bash
  sudo chmod 666 /var/run/docker.sock
  ```

### Problem 2: Dynamic Secret Resolution Failed (`vault://`)
- **Root Cause:** Invalid Vault Token or Network connection timeout to Vault Server.
- **Remediation:** Execute live diagnostic test via CLI:
  ```bash
  curl -X POST http://localhost:8000/api/v1/secrets/test \
    -H "Content-Type: application/json" \
    -d '{"provider_type": "hashicorp_vault", "vault_url": "http://127.0.0.1:8200", "auth_token": "hvs.xxxx"}'
  ```
