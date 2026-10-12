"""Docker Engine Adapter Implementation — Network Control Plane

Implements standard ProviderAdapterContract for Docker Engine runtimes.
Extracts normalized inventory snapshots for networks, subnets, and attached containers.
"""

from typing import Any, Dict, List, Optional
from app.providers.base import BaseProviderAdapter
from app.docker.client import DockerClientWrapper


class DockerAdapter(BaseProviderAdapter):
    """Provider adapter exposing capability traits for Docker Engine."""

    def __init__(self, base_url: str = "unix:///var/run/docker.sock"):
        self.client_wrapper = DockerClientWrapper(base_url=base_url)

    async def ping(self) -> bool:
        """Check provider runtime reachability."""
        return self.client_wrapper.ping()

    async def discover_networks(self) -> List[Dict[str, Any]]:
        """Discover and normalize Docker networks."""
        if not await self.ping():
            return []

        client = self.client_wrapper.get_client()
        raw_networks = client.networks.list()
        normalized_networks = []

        for net in raw_networks:
            attrs = net.attrs
            ipam = attrs.get("IPAM") or {}
            ipam_config = ipam.get("Config") or []
            subnets = []

            for cfg in ipam_config:
                subnets.append({
                    "subnet": cfg.get("Subnet"),
                    "gateway": cfg.get("Gateway"),
                    "ip_range": cfg.get("IPRange"),
                })

            normalized_networks.append({
                "provider_ref_id": attrs.get("Id"),
                "name": attrs.get("Name"),
                "driver": attrs.get("Driver"),
                "scope": attrs.get("Scope", "local"),
                "internal": attrs.get("Internal", False),
                "attachable": attrs.get("Attachable", False),
                "ingress": attrs.get("Ingress", False),
                "labels": attrs.get("Labels") or {},
                "options": attrs.get("Options") or {},
                "subnets": subnets,
            })

        return normalized_networks

    async def discover_containers(self) -> List[Dict[str, Any]]:
        """Discover and normalize Docker container workloads and network attachments."""
        if not await self.ping():
            return []

        client = self.client_wrapper.get_client()
        raw_containers = client.containers.list(all=True)
        normalized_containers = []

        for cnt in raw_containers:
            attrs = cnt.attrs
            net_settings = (attrs.get("NetworkSettings") or {}).get("Networks") or {}
            attachments = []

            for net_name, net_data in net_settings.items():
                if not net_data:
                    continue
                attachments.append({
                    "network_name": net_name,
                    "network_ref_id": net_data.get("NetworkID"),
                    "ip_address": net_data.get("IPAddress"),
                    "ipv6_address": net_data.get("GlobalIPv6Address"),
                    "mac_address": net_data.get("MacAddress"),
                    "aliases": net_data.get("Aliases") or [],
                })

            config_attr = attrs.get("Config") or {}
            state_attr = attrs.get("State") or {}

            normalized_containers.append({
                "provider_ref_id": attrs.get("Id"),
                "name": attrs.get("Name", "").lstrip("/"),
                "image": config_attr.get("Image"),
                "status": state_attr.get("Status", "unknown"),
                "labels": config_attr.get("Labels") or {},
                "attachments": attachments,
            })

        return normalized_containers

    async def discover(self) -> Dict[str, Any]:
        """Collect complete inventory snapshot from Docker Engine."""
        version_info = self.client_wrapper.get_version() if await self.ping() else {}
        networks = await self.discover_networks()
        containers = await self.discover_containers()

        return {
            "provider": "docker",
            "endpoint": self.client_wrapper.base_url,
            "version": version_info.get("Version", "unknown"),
            "os": version_info.get("Os", "unknown"),
            "arch": version_info.get("Arch", "unknown"),
            "networks": networks,
            "containers": containers,
        }

    async def inspect_network(self, network_ref_id: str) -> Dict[str, Any]:
        """Inspect low-level Docker network configuration."""
        client = self.client_wrapper.get_client()
        net = client.networks.get(network_ref_id)
        return net.attrs

    async def create_network(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Create a network on Docker Engine."""
        client = self.client_wrapper.get_client()
        net = client.networks.create(
            name=spec["name"],
            driver=spec.get("driver", "bridge"),
            internal=spec.get("internal", False),
            attachable=spec.get("attachable", False),
            labels=spec.get("labels"),
        )
        return net.attrs

    async def delete_network(self, network_ref_id: str) -> bool:
        """Delete a network on Docker Engine."""
        client = self.client_wrapper.get_client()
        net = client.networks.get(network_ref_id)
        net.remove()
        return True

    async def connect_container(self, network_ref_id: str, container_ref_id: str, ipv4_address: str | None = None, aliases: list[str] | None = None) -> bool:
        """Connect a workload container to a network with optional static IP and aliases."""
        client = self.client_wrapper.get_client()
        net = client.networks.get(network_ref_id)
        kwargs: Dict[str, Any] = {"container": container_ref_id}
        if ipv4_address:
            kwargs["ipv4_address"] = ipv4_address
        if aliases:
            kwargs["aliases"] = aliases
        net.connect(**kwargs)
        return True

    async def disconnect_container(self, network_ref_id: str, container_ref_id: str, force: bool = False) -> bool:
        """Disconnect a workload container from a network."""
        client = self.client_wrapper.get_client()
        net = client.networks.get(network_ref_id)
        net.disconnect(container_ref_id, force=force)
        return True

    async def prune_unused_networks(self) -> List[str]:
        """Prune unused networks on Docker Engine."""
        client = self.client_wrapper.get_client()
        result = client.networks.prune()
        return result.get("NetworksDeleted") or []
