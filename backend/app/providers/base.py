"""Base Provider Adapter Interface — Network Control Plane

Defines standard capability traits required by Invariant A2 for provider isolation.
All infrastructure runtimes (Docker, Podman, Kubernetes, Cloud) must implement this contract.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseProviderAdapter(ABC):
    """Abstract base class establishing provider capability trait contract."""

    @abstractmethod
    async def ping(self) -> bool:
        """Check runtime connectivity and reachability."""
        pass

    @abstractmethod
    async def discover(self) -> Dict[str, Any]:
        """Discover complete inventory snapshot (version, networks, containers/workloads)."""
        pass

    @abstractmethod
    async def discover_networks(self) -> List[Dict[str, Any]]:
        """Discover and normalize runtime network entities."""
        pass

    @abstractmethod
    async def discover_containers(self) -> List[Dict[str, Any]]:
        """Discover and normalize runtime workload/container entities."""
        pass

    @abstractmethod
    async def inspect_network(self, network_ref_id: str) -> Dict[str, Any]:
        """Inspect low-level network details from runtime."""
        pass

    @abstractmethod
    async def create_network(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Create a network resource on target runtime."""
        pass

    @abstractmethod
    async def delete_network(self, network_ref_id: str) -> bool:
        """Delete a network resource from target runtime."""
        pass

    @abstractmethod
    async def connect_container(
        self,
        network_ref_id: str,
        container_ref_id: str,
        ipv4_address: Optional[str] = None,
        aliases: Optional[List[str]] = None,
    ) -> bool:
        """Attach a workload container/pod to a virtual network."""
        pass

    @abstractmethod
    async def disconnect_container(
        self,
        network_ref_id: str,
        container_ref_id: str,
        force: bool = False,
    ) -> bool:
        """Detach a workload container/pod from a virtual network."""
        pass

    @abstractmethod
    async def prune_unused_networks(self) -> List[str]:
        """Prune unused networks from target runtime."""
        pass
