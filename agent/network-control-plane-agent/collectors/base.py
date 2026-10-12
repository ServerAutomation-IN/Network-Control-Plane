"""Base Runtime Collector Interface — network-control-plane-agent

Defines the pluggable collector contract for host workload and network discovery,
runtime event streaming, and imperative command execution.
"""

from abc import ABC, abstractmethod
import socket
import time
from typing import Any, Dict, List


class BaseRuntimeCollector(ABC):
    """Abstract base class defining capability contracts for host runtime collectors."""

    def __init__(self, socket_path: str | None = None):
        self.socket_path = socket_path

    @property
    @abstractmethod
    def runtime_name(self) -> str:
        """Normalized runtime identifier (e.g. 'docker', 'podman', 'hyperv', 'linux')."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this runtime engine is present and responsive on the host system."""
        pass

    @abstractmethod
    def get_runtime_info(self) -> Dict[str, Any]:
        """Return runtime metadata and host environmental telemetry."""
        pass

    @abstractmethod
    def collect_networks(self) -> List[Dict[str, Any]]:
        """Discover virtual networks, subnets, bridges, and IPAM pools."""
        pass

    @abstractmethod
    def collect_workloads(self) -> List[Dict[str, Any]]:
        """Discover containers or virtual machines and attached network endpoints."""
        pass

    def stream_events(self):
        """Yield real-time network and workload lifecycle events."""
        return []

    def execute_command(self, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute imperative mutation command on the local runtime engine.

        Supported standard actions:
        - PING: Reachability and health probe
        - CREATE_NETWORK: Allocate virtual network / bridge
        - DELETE_NETWORK: Remove virtual network / bridge
        - ATTACH_ENDPOINT: Connect workload to network
        - DETACH_ENDPOINT: Disconnect workload from network
        """
        action_upper = action.upper()
        if action_upper == "PING":
            return {
                "pong": True,
                "runtime": self.runtime_name,
                "hostname": socket.gethostname(),
                "timestamp": time.time(),
            }
        raise NotImplementedError(
            f"Action '{action}' is not supported by runtime collector '{self.runtime_name}'"
        )
