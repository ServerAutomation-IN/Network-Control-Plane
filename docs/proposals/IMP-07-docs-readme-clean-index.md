# Proposal IMP-07: Central Documentation Index Cleanup & Broken Links Remediation

**Status:** ✅ IMPLEMENTED  
**Target Component:** `docs/README.md`  
**Priority:** Medium  
**Estimated Effort:** Low (30 mins)  
**Implementation Date:** 2026-10-12  

---

## 1. Problem Statement
* In accordance with standard product release governance, internal marketing kits (`Social_and_Community_Distribution_Kit.md`, `Launch_Playbook_and_Checklist.md`), sprint backlogs (`Tasks.md`, `MVP_Definitions.md`, `Epics.md`), and redundant 10-line stubs (`architecture/components.md`, `architecture/data-model.md`) were added to `.gitignore` and excluded from git tracking to prevent noise.
* However, [`docs/README.md`](file:///c:/Users/vsrivastava/Documents/GH-ServerAutomation-IN/Network-Control-Plane/docs/README.md) still contains 7 active hyperlinks pointing directly to these excluded files:
  1. `announcements/Social_and_Community_Distribution_Kit.md`
  2. `announcements/Launch_Playbook_and_Checklist.md`
  3. `architecture/components.md`
  4. `architecture/data-model.md`
  5. `roadmap/MVP_Definitions.md`
  6. `roadmap/Epics.md`
  7. `implementation/Tasks.md`
* When consumers or developers navigate `docs/README.md` in a cloned repo or on GitHub, these 7 links will fail with HTTP 404 / broken file errors.
* Furthermore, the newly introduced architectural proposals directory ([`docs/proposals/`](file:///c:/Users/vsrivastava/Documents/GH-ServerAutomation-IN/Network-Control-Plane/docs/proposals/)) is not currently indexed in `docs/README.md`.

---

## 2. Proposed Solution
Update [`docs/README.md`](file:///c:/Users/vsrivastava/Documents/GH-ServerAutomation-IN/Network-Control-Plane/docs/README.md) to maintain an authoritative, clean navigation index containing only committed, production-grade release documents.

### Proposed Structure for `docs/README.md`:
1. **Product Announcements & Release Notes:**
   - Link `announcements/v1.0.0-GA-Launch-Announcement.md`.
   - Remove internal social kit and launch playbook links.
2. **Product Release & User Documentation:**
   - Maintain `deployment/Deployment_and_Configuration_Guide.md`.
   - Maintain `user-guide/User_Guide.md`.
   - Maintain `user-guide/Okta_SSO_Configuration_Guide.md`.
3. **Architecture & Master Specifications:**
   - Maintain `product/Blueprint.md`.
   - Maintain `architecture/Architecture.md`.
   - Maintain `requirements/Requirements.md`.
   - Maintain `product/Problem_Statement.md`.
   - Maintain `product/vision.md`.
   - Remove redundant component and data-model stub links (referencing `Architecture.md` directly).
4. **Architecture Decision Records (ADRs):**
   - Maintain `adr/` index (`ADR-001` through `ADR-004`).
5. **Roadmap & Release Sequence:**
   - Maintain `roadmap/roadmap.md`.
   - Remove internal `MVP_Definitions.md` and `Epics.md` sprint checklists.
6. **Improvement Proposals & RFCs (`docs/proposals/`):**
   - Add new section indexing `docs/proposals/` for active architectural proposals (`IMP-01` through `IMP-07`).

---

## 3. Implementation Steps
1. Edit `docs/README.md` to remove the 7 broken links.
2. Add the `docs/proposals/` index section.
3. Validate all markdown links resolve correctly against the active Git file tree.
