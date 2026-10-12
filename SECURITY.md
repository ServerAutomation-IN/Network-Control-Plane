# Security Policy

## Supported Versions

| Version    | Supported          |
| ---------- | ------------------ |
| v1.0.0-GA  | :white_check_mark: |
| < v1.0.0   | :x:                |

## Reporting a Vulnerability

The **Network Control Plane** team takes security vulnerabilities seriously. If you discover a vulnerability, please report it privately:

1. **GitHub Security Advisory (Recommended):** Submit a confidential advisory via [GitHub Security Advisories](https://github.com/ServerAutomation-IN/Network-Control-Plane/security/advisories/new).
2. **Email Disclosure:** Send details to `security@network-control-plane.org`.

### Response Timeline
- **Initial Acknowledgment:** Within 48 hours.
- **Triage & Severity Assessment:** Within 3 business days.
- **Fix & Disclosure Coordination:** Within 14 business days (or coordinated embargo date).

Please do NOT disclose security vulnerabilities publicly in issues or discussions until an official security release has been made available.

---

## Operational Hardening & Secret Management

Network Control Plane enforces strict guidelines regarding credential protection:
- **Zero Plaintext Secrets in Repositories:** Never commit `.env` files, passwords, or provider API tokens to version control.
- **Strict File ACLs:** Environment configuration files (`.env`) must have strict filesystem permissions (`chmod 600` on Linux, `icacls` on Windows).
- **Dynamic Key Vault Resolution:** Production deployments are encouraged to use dynamic URI references (`vault://`, `aws-secret://`, `azure-vault://`) rather than static environment variables.

For detailed playbooks, see:
- [Deployment & Configuration Guide — Production Secrets Hardening Playbook](docs/deployment/Deployment_and_Configuration_Guide.md#41-production-secrets-management--permissions-hardening-playbook)
- [Okta SSO Configuration Guide — Security Best Practices](docs/user-guide/Okta_SSO_Configuration_Guide.md#step-3-configure-network-control-plane--secure-secret-management)
