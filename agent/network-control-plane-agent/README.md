# Host Agent — network-control-plane-agent

Provider host agent daemon for Network Control Plane. Supports remote network and workload discovery, telemetry streaming, and bidirectional mutation operations across heterogeneous container and virtualization runtimes.

---

## Supported Runtime Engines

The agent uses a pluggable collector architecture (`collectors/`) capable of discovering and managing:

1. **Docker Engine (`docker`):** Standard Docker Engine daemon via local UNIX socket or TCP (`docker.sock`).
2. **Podman (`podman`):** Podman Netavark/CNI network bridges and container workloads via rootful (`/run/podman/podman.sock`) or rootless user sockets.
3. **Microsoft Hyper-V (`hyperv`):** Windows Server and client Hyper-V Virtual Switches (External, Internal, Private) and VM virtual network adapters.
4. **Linux Native Bridges (`linux`):** Host-level kernel bridges (`br0`, `cni0`, `docker0`), `veth` pairs, and VLANs discovered via `/sys/class/net` and netlink.

---

## CLI Usage

```bash
# Auto-detect responsive local runtime engine (Docker -> Podman -> Hyper-V -> Linux)
python main.py --host-id host-edge-01 --control-plane-url https://ncp.example.com --api-token <TOKEN>

# Explicitly target Podman rootless socket
python main.py --runtime podman --socket-path unix:///run/user/1000/podman/podman.sock --api-token <TOKEN>

# Explicitly target Microsoft Hyper-V Virtual Switches on Windows
python main.py --runtime hyperv --api-token <TOKEN>

# Explicitly target native Linux host bridges
python main.py --runtime linux --api-token <TOKEN>
```
