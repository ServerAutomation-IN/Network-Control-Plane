# Proposal IMP-08: Transition to Apache License 2.0 for Patent Protection & Retaliation Defense

**Status:** ✅ IMPLEMENTED  
**Target Component:** `LICENSE`, `CITATION.cff`, `README.md`  
**Priority:** High  
**Estimated Effort:** Low (30 mins)  
**Implementation Date:** 2026-10-12  

---

## 1. Problem Statement & Legal Requirement
* **User Requirement:** "The license must ensure that no one can patent this product."
* **Current State:** The repository currently uses the [**MIT License**](file:///c:/Users/vsrivastava/Documents/GH-ServerAutomation-IN/Network-Control-Plane/LICENSE).
* **The Vulnerability of MIT:**
  - The MIT License is a short copyright license that **does NOT contain an express patent grant or patent retaliation/defense clause**.
  - Under MIT, an entity could fork or contribute to the project, file software patents on network control plane concepts or algorithms, and later assert patent infringement claims against downstream users, contributors, or the platform itself.

---

## 2. Proposed Solution: Adopt Apache License, Version 2.0 (Apache-2.0)
The **Apache License, Version 2.0** is the industry standard permissive open-source license designed specifically to prevent patent capture, used by leading infrastructure projects (Kubernetes, Docker/Moby, Envoy, OpenTelemetry, Apache Kafka):

### Key Patent Protections in Apache 2.0:
1. **Section 3 (Grant of Patent License):**
   > *"Each Contributor hereby grants to You a perpetual, worldwide, non-exclusive, no-charge, royalty-free, irrevocable patent license to make, have made, use, offer to sell, sell, import, and otherwise transfer the Work..."*
   - Any contributor or entity contributing code automatically grants an irrevocable patent license to all users and contributors.
2. **Section 3 (Patent Termination / Retaliation Defense):**
   > *"If You institute patent litigation against any entity... alleging that the Work or a Contribution incorporated within the Work constitutes direct or contributory patent infringement, then any patent licenses granted to You under this License for that Work shall terminate as of the date such litigation is filed."*
   - If a party attempts to patent or assert patent claims against the product, their patent license is revoked immediately.

---

## 3. Implementation Steps
1. Replace [`LICENSE`](file:///c:/Users/vsrivastava/Documents/GH-ServerAutomation-IN/Network-Control-Plane/LICENSE) with the official Apache License, Version 2.0 text (Copyright 2026 Network Control Plane Contributors).
2. Update [`CITATION.cff`](file:///c:/Users/vsrivastava/Documents/GH-ServerAutomation-IN/Network-Control-Plane/CITATION.cff) (`license: Apache-2.0`).
3. Update root [`README.md`](file:///c:/Users/vsrivastava/Documents/GH-ServerAutomation-IN/Network-Control-Plane/README.md):
   - Update shield badge from MIT to Apache-2.0.
   - Update Section 12 (License) to specify Apache 2.0.
