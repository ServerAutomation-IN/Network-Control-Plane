# Contributing to Network Control Plane

Thank you for your interest in contributing to **Network Control Plane**! We are committed to fostering an open, collaborative, and architecturally disciplined community.

---

## 🏛️ Architectural Invariants & Rules

Every contribution must strictly adhere to our core architectural invariants:

1. **A1 — Provider Neutrality:** Core domain models and services (`backend/app/models/`, `schemas/`, `services/`, `inventory/`, `ipam/`, `policy/`) must **NEVER** import provider-specific SDKs (`docker`, `kubernetes`, `boto3`). All provider logic lives strictly within provider adapters (`backend/app/docker/`, `app/podman/`, etc.).
2. **A2 — Adapter Isolation:** Adapters interact with the control plane through standard capability contracts (`discover`, `inspect`, `create_network`, `delete_network`, `attach_endpoint`, `detach_endpoint`).
3. **A3 — Read Before Write & Safety:** Any operation mutating network state must execute pre-flight safety risk evaluation (`LOW` to `CRITICAL`) and record an immutable `AuditEvent`.
4. **A4 — API Socket Isolation:** The frontend client never communicates directly with host sockets or provider APIs.
5. **Product Descriptor:** The neutral descriptor is strictly **Network Control Plane** (*Docknet is NOT the name*).

---

## 🛠️ Local Development & Testing

### Backend Setup
```bash
cd backend
python -m venv .venv
# On Windows: .\.venv\Scripts\activate
# On Linux/macOS: source .venv/bin/activate
pip install uv
uv pip install -e ".[dev]"

# Run backend tests
pytest -v
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev

# Run build & type checking
npm run build
```

---

## 📋 Pull Request Workflow

1. **Fork the Repository:** Fork `https://github.com/ServerAutomation-IN/Network-Control-Plane` and clone your fork.
2. **Create a Topic Branch:** Create a branch from `main` using descriptive naming conventions:
   - Features: `git checkout -b feature/your-feature-name`
   - Bug fixes: `git checkout -b fix/issue-description`
   - Documentation: `git checkout -b docs/topic-description`
3. **Adhere to Standards:** Follow strict typing in Python (type hints, Pydantic v2) and TypeScript (no `any`).
4. **Test Thoroughly:** Ensure all unit and integration tests pass before submitting (`pytest -v` and `npm run build`).
5. **Submit Pull Request:** Fill out the [Pull Request Template](.github/pull_request_template.md).

---

## 💡 Architectural Proposals & RFCs

For large-scale architectural changes, new provider adapters, or data model migrations:
- Review existing proposals in [`docs/proposals/`](docs/proposals/).
- Open an RFC proposal using the standard format before writing large code contributions to ensure alignment with project invariants (A1–A4).

