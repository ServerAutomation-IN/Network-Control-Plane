# Proposal IMP-09: Root README Documentation Index Cleanup & Broken Links Remediation

**Status:** ✅ IMPLEMENTED  
**Target Component:** `README.md`  
**Priority:** Medium  
**Estimated Effort:** Low (20 mins)  
**Implementation Date:** 2026-10-12  

---

## 1. Problem Statement
* Following the exclusion of internal marketing materials and sprint backlog files from Git tracking, root [`README.md`](file:///c:/Users/vsrivastava/Documents/GH-ServerAutomation-IN/Network-Control-Plane/README.md) still contains 4 active links pointing to files now ignored by `.gitignore`:
  1. `docs/announcements/Social_and_Community_Distribution_Kit.md` (Line 130)
  2. `docs/announcements/Launch_Playbook_and_Checklist.md` (Line 131)
  3. `docs/roadmap/MVP_Definitions.md` (Line 144)
  4. `docs/roadmap/Epics.md` (Line 146)
* In the public GitHub repository or release distribution, clicking these links will produce 404 Not Found errors.
* Additionally, root `README.md` does not currently reference the proposals directory ([`docs/proposals/`](file:///c:/Users/vsrivastava/Documents/GH-ServerAutomation-IN/Network-Control-Plane/docs/proposals/)).

---

## 2. Proposed Solution
Update Section 8 ("Product Documentation Index") of root [`README.md`](file:///c:/Users/vsrivastava/Documents/GH-ServerAutomation-IN/Network-Control-Plane/README.md):
1. **Remove broken links:**
   - Under Launch & Announcements: Retain only the official `docs/announcements/v1.0.0-GA-Launch-Announcement.md`.
   - Under Roadmap & Release History: Retain `CHANGELOG.md` and `docs/roadmap/roadmap.md`. Remove internal `MVP_Definitions.md` and `Epics.md`.
2. **Add Architectural Proposals Section:**
   - Link to `docs/proposals/` for active platform RFCs and upcoming capabilities.

---

## 3. Implementation Steps
1. Edit root `README.md` lines 128–147.
2. Verify all markdown link paths correspond strictly to tracked files in git.
