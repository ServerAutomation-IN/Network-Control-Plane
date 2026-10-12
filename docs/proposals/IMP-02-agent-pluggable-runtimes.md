# Proposal IMP-02: Multi-Runtime Pluggable Collectors for Host Agent

**Status:** ✅ IMPLEMENTED  
**Target Component:** `agent/network-control-plane-agent/`  
**Priority:** Medium-High  
**Estimated Effort:** Medium (2–3 days)  

---

## 1. Problem Statement
Currently, `agent/network-control-plane-agent/daemon.py` directly executes `import docker` and invokes `client = docker.from_env()`.
* It fails or defaults to a hardcoded fallback on systems running **Podman** (`/run/podman/podman.sock` or rootless).
* It cannot monitor standalone **Microsoft Hyper-V** hosts (e.g., Windows Server without SCVMM).
* It cannot discover host-level **Linux Bridges** (`br0`, `veth`, `ovs`, CNI interfaces).

---

## 2. Proposed Architecture: Pluggable Collector Pattern

Refactor the discovery logic into an extensible collector interface:

```text
agent/network-control-plane-agent/
├── collectors/
│   ├── base.py              # BaseRuntimeCollector interface
│   ├── docker_collector.py  # Standard Docker Engine collector
│   ├── podman_collector.py  # Podman API / socket collector
│   ├── hyperv_collector.py  # PowerShell / WMI Hyper-V Virtual Switch collector
│   └── linux_collector.py   # iproute2 / sysfs native network collector
├── daemon.py                # Collector orchestrator
└── main.py                  # Auto-detection CLI
```

### Collector Interface (`BaseRuntimeCollector`)
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseRuntimeCollector(ABC):
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this runtime engine is present and responsive on the host."""
        pass

    @abstractmethod
    def collect_networks(self) -> List[Dict[str, Any]]:
        """Discover virtual networks, subnets, and bridges."""
        pass

    @abstractmethod
    def collect_workloads(self) -> List[Dict[str, Any]]:
        """Discover containers/VMs and attached network interfaces."""
        pass

    @abstractmethod
    def stream_events(self):
        """Yield real-time network and workload lifecycle events."""
        pass
```

---

## 3. Benefits & Value
1. **True Cross-Platform Support:** The exact same Python agent binary runs on Ubuntu, RHEL (Podman-native), and Windows Server (Hyper-V native).
2. **Auto-Detection:** When launched with `--auto-detect`, the agent probes available sockets and initializes the active collector without manual flags.
3. **Graceful Fallbacks:** If Docker is restarted, the collector reconnects automatically without crashing the agent process.
