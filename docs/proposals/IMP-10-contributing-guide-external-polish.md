# Proposal IMP-10: Contributing Guide External Contributor Workflow Polish

**Status:** ✅ IMPLEMENTED  
**Target Component:** `CONTRIBUTING.md`, `.github/pull_request_template.md`  
**Priority:** Low  
**Estimated Effort:** Low (15 mins)  
**Implementation Date:** 2026-10-12  

---

## 1. Problem Statement
* In [`CONTRIBUTING.md`](file:///c:/Users/vsrivastava/Documents/GH-ServerAutomation-IN/Network-Control-Plane/CONTRIBUTING.md) line 49, the branch naming convention instructs contributors:
  ```bash
  git checkout -b feature/P0X-xxx-description
  ```
* `P0X-xxx` refers to internal MVP sprint task identifiers (e.g. `P00-001`, `P02-005` from `Tasks.md`), which are internal sprint tracking IDs now excluded from the public release.
* External open-source contributors will not have context on internal `P0X` numbers.

---

## 2. Proposed Solution
Update `CONTRIBUTING.md` Section 3 ("Pull Request Workflow"):
1. Generalize branch naming convention:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/issue-description
   ```
2. Mention the RFC proposal workflow (`docs/proposals/`) for large architectural changes.

---

## 3. Implementation Steps
1. Edit `CONTRIBUTING.md` line 49.
2. Add a brief note directing large architectural changes to `docs/proposals/`.
