# Okta SSO Configuration & User Onboarding Guide — Network Control Plane

This guide provides end-to-end instructions for platform administrators to configure **Okta Single Sign-On (SSO)** via OpenID Connect (OIDC) for automated user registration (Just-In-Time provisioning) and governed login in **Network Control Plane**.

---

## 🏛️ Architecture & Authentication Flow

Network Control Plane uses standard **OAuth 2.0 / OpenID Connect (OIDC)** Authorization Code flow paired with **Just-In-Time (JIT) User Provisioning**:

```text
┌─────────────────┐       1. Click "Okta SSO Gateway"       ┌────────────────────────────────┐
│   User Browser  │ ───────────────────────────────────────> │  Network Control Plane Frontend│
└─────────────────┘                                          └──────────────┬─────────────────┘
         │                                                                  │
         │ 2. Redirect to Okta (/protocol/openid-connect/auth)              │ 3. Fetch Auth URL
         ▼                                                                  ▼
┌─────────────────┐                                          ┌────────────────────────────────┐
│ Okta Identity   │                                          │  FastAPI Backend API Gateway   │
│ Provider (IdP)  │                                          │   (/api/v1/auth/login/okta)    │
└─────────────────┘                                          └────────────────────────────────┘
         │
         │ 4. User logs in with Okta credentials & MFA
         │ 5. Redirect back to /auth/callback?code=AUTH_CODE
         ▼
┌─────────────────┐       6. Exchange code for JWT tokens    ┌────────────────────────────────┐
│   User Browser  │ ───────────────────────────────────────> │  Network Control Plane Backend │
└─────────────────┘                                          │  (/api/v1/auth/callback/okta)  │
                                                             └──────────────┬─────────────────┘
                                                                            │
                                                                            │ 7. Query UserInfo (/userinfo)
                                                                            │ 8. Map Okta roles -> RBAC
                                                                            │ 9. JIT Register User in DB
                                                                            │ 10. Issue Platform JWT Token
                                                                            ▼
                                                             ┌────────────────────────────────┐
                                                             │     PostgreSQL 16 DB Store     │
                                                             │   (users table, AuditEvent)    │
                                                             └────────────────────────────────┘
```

### Key Principles
1. **Zero Password Storage for SSO Users:** User credentials never touch Network Control Plane servers; passwords remain protected in Okta.
2. **Just-In-Time (JIT) Automatic Registration:** When an authorized user logs in via Okta for the first time, an account is automatically created in PostgreSQL and an immutable `AuditEvent` (`JIT_SSO_USER_REGISTRATION`) is logged.
3. **Role-Based Access Control (RBAC):** Group memberships configured in Okta are automatically mapped to platform roles (`admin`, `operator`, `viewer`).

---

## 📋 Prerequisites

Before you begin, ensure you have:
1. **Okta Administrative Access:** An active Okta tenant (Workforce Identity Cloud or Okta Developer account).
2. **Network Control Plane Admin Privileges:** An administrator account or server configuration access (`.env` file).
3. **Control Plane Host Domain:** The public or internal URL where the frontend is accessible (e.g. `http://localhost:3001` or `https://ncp.corp.internal`).

---

## Step 1: Create an OIDC Web Application in Okta

1. Sign in to your **Okta Admin Console** (`https://<your-org>-admin.okta.com`).
2. In the left navigation menu, navigate to **Applications** > **Applications**.
3. Click **Create App Integration**.
4. Configure integration type:
   - **Sign-in method:** Select **OIDC - OpenID Connect**.
   - **Application type:** Select **Web Application**.
   - Click **Next**.
5. Configure Application Settings:
   - **App integration name:** `Network Control Plane`
   - **Logo (optional):** Upload the Network Control Plane icon.
   - **Client definition:** Select **Use Okta-generated client ID** *(Okta assigns and manages the client credentials)*.
   - **Client authentication:** Select **Client secret**.
   - **Grant type:** Check **Authorization Code**.
6. Configure Redirect URIs:
   - **Sign-in redirect URIs:** Add your frontend callback URL:
     ```text
     http://localhost:3001/auth/callback
     ```
     *(If using a custom domain, use `https://<your-domain>/auth/callback`)*
   - **Sign-out redirect URIs:** Add your frontend home URL:
     ```text
     http://localhost:3001/
     ```
7. Configure Assignments:
   - Under **Controlled access**, choose:
     - **Allow everyone in your organization to access** (or select specific security groups).
8. Click **Save**.
9. In the newly created application's **General** tab:
   - Copy the **Client ID** (e.g., `0oa1a2b3c4d5e6f7g8h9`).
   - Copy the **Client Secret** (click the eye icon or copy button).
   - Under **General Settings** > **Issuer**, note the **Okta Domain** / **Issuer URL** (e.g., `https://dev-123456.okta.com/oauth2/default`).

---

## Step 2: Configure Group & Role Claims in Okta

Network Control Plane evaluates user permissions using the `roles` or `groups` claim returned in the OIDC ID Token or UserInfo endpoint:

| Okta Group / Role Name | Network Control Plane Role | Capabilities |
|---|---|---|
| `Network-Admins` or `admin` | **admin** | Full read/write, policy editing, host management, user administration |
| `Network-Operators` or `operator` | **operator** | Create/delete networks, connect containers, trigger GitOps reconciliation |
| `Network-Viewers` or default | **viewer** | Read-only inspection of topology, IPAM, and policies |

### Configuring the Claims in Okta:
1. In the Okta Admin Console, navigate to **Security** > **API** > **Authorization Servers**.
2. Select your Authorization Server (typically `default`).
3. Click the **Claims** tab.
4. Click **Add Claim**:
   - **Name:** `roles`
   - **Include in token type:** `ID Token` & `Userinfo`
   - **Value type:** `Groups`
   - **Filter:** Select `Matches regex` and enter `.*` (or `(admin|operator|viewer|Network-.*)`).
5. Click **Create**.

---

## Step 3: Configure Network Control Plane & Secure Secret Management

You can configure Okta SSO using **Method A (Environment Variables & Docker)** or **Method B (Web UI & REST API)**.

---

### 🔒 Security Best Practices: Storing Okta Credentials

> [!CAUTION]
> **Never commit secrets to Git or hardcode them directly into `docker-compose.yml`!**
> Committing `OKTA_CLIENT_SECRET` exposes administrative identity credentials to unauthorized team members, automated CI/CD runners, and git history leaks.

Follow the **Three-Tier Security Model** based on your environment:

#### Tier 1 (Recommended for Standalone Docker Compose & Dev/Staging): Git-Ignored `.env` + File Permissions Hardening

1. **Use Variable Interpolation in `deployment/docker-compose.yml`:**
   Keep `docker-compose.yml` clean by using environment variable references:
   ```yaml
   services:
     backend:
       environment:
         - OKTA_ISSUER_URL=${OKTA_ISSUER_URL}
         - OKTA_CLIENT_ID=${OKTA_CLIENT_ID}
         - OKTA_CLIENT_SECRET=${OKTA_CLIENT_SECRET}
         - OKTA_ROLE_CLAIM=${OKTA_ROLE_CLAIM:-roles}
   ```

2. **Populate `deployment/.env` from the provided template:**
   ```bash
   cp deployment/.env.example deployment/.env
   ```
   Edit `deployment/.env` and supply your actual credentials:
   ```bash
   OKTA_ISSUER_URL=https://<your-okta-domain>.okta.com/oauth2/default
   OKTA_CLIENT_ID=0oa1a2b3c4d5e6f7g8h9
   OKTA_CLIENT_SECRET=your_confidential_okta_client_secret_here
   OKTA_ROLE_CLAIM=roles
   ```

3. **Harden Filesystem Permissions (Restrict Read/Write to Current User Only):**
   - **Linux / macOS:**
     ```bash
     chmod 600 deployment/.env
     ```
   - **Windows (PowerShell):**
     *(On Windows, `chmod` is not supported. Use `icacls` to strip inherited permissions and grant exclusive Read/Write access to the active user)*
     ```powershell
     icacls deployment\.env /inheritance:r /grant:r "$($env:USERNAME):(R,W)"
     ```

4. **Start or Restart the Backend:**
   ```bash
   docker compose -f deployment/docker-compose.yml restart backend
   ```

---

#### Tier 2 (Recommended for Production Docker Swarm / Kubernetes): Native Secrets

Docker and Kubernetes secrets prevent sensitive values from appearing in `docker inspect <container>`, process table dumps (`ps aux`), or crash logs.

1. **Store Secret in a Protected File or Key Vault:**
   ```bash
   echo "your_confidential_okta_client_secret_here" > /run/secrets/okta_client_secret
   chmod 400 /run/secrets/okta_client_secret
   ```

2. **Mount via `docker-compose.yml` Secrets Engine:**
   ```yaml
   services:
     backend:
       secrets:
         - okta_client_secret
       environment:
         - OKTA_ISSUER_URL=${OKTA_ISSUER_URL}
         - OKTA_CLIENT_ID=${OKTA_CLIENT_ID}
         - OKTA_CLIENT_SECRET_FILE=/run/secrets/okta_client_secret
         - OKTA_ROLE_CLAIM=roles

   secrets:
     okta_client_secret:
       file: ./secrets/okta_client_secret.txt
   ```

---

#### Tier 3 (Zero-Trust Enterprise): Dynamic Key Vault Secret URI Resolution

For high-security enterprises requiring automated rotation and zero local disk persistence, Network Control Plane includes a native **Key Vault Secrets Resolver**:

1. Instead of entering the raw client secret, configure `OKTA_CLIENT_SECRET` with a dynamic Vault URI:
   ```bash
   # HashiCorp Vault KV v2:
   OKTA_CLIENT_SECRET=vault://secret/data/sso#client_secret

   # AWS Secrets Manager:
   OKTA_CLIENT_SECRET=aws-secret://production/sso/okta#client_secret

   # Azure Key Vault:
   OKTA_CLIENT_SECRET=azure-vault://ncp-okta-client-secret
   ```

2. Network Control Plane automatically resolves and decrypts the secret in-memory over mutual TLS at runtime. No credentials ever touch host disks or environment logs.

---

### Method B: Configure via Web UI or REST API

Administrators can also update the Okta integration at runtime without restarting containers:

#### Via REST API:
```bash
curl -X PUT "http://localhost:8000/api/v1/auth/providers/okta" \
  -H "Authorization: Bearer <your-admin-jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "issuer_url": "https://<your-okta-domain>.okta.com/oauth2/default",
    "client_id": "<your-okta-client-id>",
    "client_secret": "<your-okta-client-secret>",
    "role_claim_path": "roles"
  }'
```

#### Via Web Dashboard:
1. Log into Network Control Plane as an Administrator.
2. Navigate to **Settings & Integrations** > **Enterprise SSO**.
3. Select **Okta SSO**.
4. Test token generation with the **Interactive SSO Simulator**.

---

## Step 4: User Registration & Sign-In Workflow

Once configured, users can log into Network Control Plane using Okta:

1. **Access Login Screen:** Navigate to `http://localhost:3001` in your browser.
2. **Select SSO:** Click on the **Enterprise SSO** tab.
3. **Click Okta Gateway:** Click **Okta SSO Gateway**.
4. **Authenticate in Okta:** The browser redirects to your organization's Okta sign-in page with MFA enforcement.
5. **JIT User Provisioning:**
   - Okta redirects back to `http://localhost:3001/auth/callback?code=...`.
   - The backend validates the authorization code against Okta's token endpoint.
   - The backend checks if the user exists in the PostgreSQL `users` table:
     - **If first time:** A new record is inserted with the user's Okta username, corporate email, and mapped role.
     - **If returning user:** The `last_login` timestamp and role mappings are updated.
   - An immutable `AuditEvent` is recorded.
6. **Dashboard Access:** A secure JWT token is issued, and the user is redirected straight into the Network Control Plane dashboard.

---

## 🔍 Verification & Troubleshooting

### 1. Verify Configured Providers
Query the backend to confirm Okta is registered and active:
```bash
curl -s http://localhost:8000/api/v1/auth/providers | jq .
```
*Expected response:*
```json
[
  {
    "id": "okta",
    "name": "Okta SSO",
    "issuer_url": "https://<your-okta-domain>.okta.com/oauth2/default",
    "client_id": "<your-okta-client-id>",
    "enabled": true
  }
]
```

### 2. Common Errors & Fixes

| Issue | Cause | Resolution |
|---|---|---|
| `redirect_uri_mismatch` | Okta redirect URI doesn't match frontend URL | Verify in Okta App that **Sign-in redirect URI** matches `http://localhost:3001/auth/callback` exactly (including port and protocol). |
| User assigned `viewer` role instead of `admin` | Claim mapping missing or group name mismatch | Verify that the `roles` claim is added to the ID Token in Okta Authorization Server, and the user belongs to a group containing `admin` or `operator`. |
| `invalid_client` or `401 Unauthorized` | Client Secret is expired or incorrect | Verify and re-copy the Client Secret from the Okta application's **General** tab. |
| Browser stays on `/auth/callback` | Network connectivity between backend and Okta | Verify the Network Control Plane backend container can reach `https://<your-okta-domain>.okta.com` over outbound HTTPS (port 443). |

---

## 📄 Related Documentation
- [Deployment & Configuration Guide](../deployment/Deployment_and_Configuration_Guide.md)
- [System Architecture Specification](../architecture/Architecture.md)
- [User Guide](User_Guide.md)
