## Description

Please include a summary of the change and the related issue or proposal ID (e.g., `#123` or `IMP-XX`).

Fixes #(issue)

## Type of Change

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Refactoring / Performance improvement

## Architectural Invariants & Quality Checklist

Please confirm compliance with the project directives in [AGENTS.md](file:///c:/Users/vsrivastava/Documents/GH-ServerAutomation-IN/Network-Control-Plane/AGENTS.md):

- [ ] **A1 — Provider Neutrality:** Core domain models and services (`backend/app/models/`, `schemas/`, `services/`) do NOT import provider-specific SDKs (`docker`, `kubernetes`).
- [ ] **A2 — Adapter Isolation:** Provider interactions conform to standardized provider adapter contracts.
- [ ] **A3 — Read Before Write:** Mutating actions execute validation, pre-flight safety risk evaluation, and record an `AuditEvent`.
- [ ] **A4 — API Socket Isolation:** Frontend client never communicates directly with Docker sockets or provider APIs.
- [ ] **Naming:** No references to deprecated names exist (descriptor is strictly **Network Control Plane**).
- [ ] **Typing:** Strict typing adhered to (Python type hints / Pydantic models, TypeScript without `any`).
- [ ] **Testing:** Unit or integration tests have been added or updated in `backend/tests/` or `frontend/src/tests/`.
- [ ] **Verification:** All tests run cleanly (`pytest -v` and `npm run build`).
