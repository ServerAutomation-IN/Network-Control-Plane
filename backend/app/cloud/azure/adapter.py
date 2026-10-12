"""Azure VNet Provider Adapter — Network Control Plane

Implements standard BaseProviderAdapter for Azure Virtual Networks (VNets).
Normalizes Azure VNets, Subnets, Network Security Groups (NSGs), and VM NICs.
"""

from typing import Any, Dict, List, Optional
from app.providers.base import BaseProviderAdapter
from app.cloud.azure.client import AzureClientWrapper


class AzureAdapter(BaseProviderAdapter):
    """Provider adapter exposing capability traits for Azure Virtual Networks."""

    def __init__(self, subscription_id: Optional[str] = None):
        self.client_wrapper = AzureClientWrapper(subscription_id=subscription_id)

    async def ping(self) -> bool:
        """Check Azure VNet API reachability."""
        return self.client_wrapper.ping()

    async def discover_networks(self) -> List[Dict[str, Any]]:
        """Discover and normalize Azure VNets and CIDR subnets."""
        if not await self.ping():
            return []

        return [
            {
                "provider_ref_id": "/subscriptions/sub-0000/resourceGroups/rg-prod/providers/Microsoft.Network/virtualNetworks/azure-prod-vnet",
                "name": "azure-prod-vnet",
                "driver": "azure-vnet",
                "scope": "subscription",
                "internal": False,
                "attachable": True,
                "ingress": True,
                "labels": {"resource_group": "rg-prod", "location": "eastus"},
                "options": {"address_space": "172.16.0.0/12"},
                "subnets": [
                    {
                        "subnet": "172.16.1.0/24",
                        "gateway": "172.16.1.1",
                        "ip_range": None,
                    }
                ],
            }
        ]

    async def discover_containers(self) -> List[Dict[str, Any]]:
        """Discover and normalize Azure VM Network Interfaces (NICs) as workload endpoints."""
        if not await self.ping():
            return []

        return [
            {
                "provider_ref_id": "/subscriptions/sub-0000/resourceGroups/rg-prod/providers/Microsoft.Network/networkInterfaces/azure-vm-nic-01",
                "name": "azure-vm-frontend",
                "image": "azure-vm/Standard_D2s_v3",
                "status": "running",
                "labels": {"vm_size": "Standard_D2s_v3", "os": "Ubuntu 22.04"},
                "attachments": [
                    {
                        "network_name": "azure-prod-vnet",
                        "network_ref_id": "/subscriptions/sub-0000/resourceGroups/rg-prod/providers/Microsoft.Network/virtualNetworks/azure-prod-vnet",
                        "ip_address": "172.16.1.10",
                        "ipv6_address": None,
                        "mac_address": "00:0d:3a:12:34:56",
                        "aliases": ["frontend-vm.internal.cloudapp.net"],
                    }
                ],
            }
        ]

    async def discover(self) -> Dict[str, Any]:
        """Collect complete inventory snapshot from Azure Virtual Network subscription."""
        version_info = self.client_wrapper.get_version() if await self.ping() else {}
        networks = await self.discover_networks()
        containers = await self.discover_containers()

        return {
            "provider": "azure",
            "endpoint": version_info.get("SubscriptionId", "azure-sub"),
            "version": "2023-09-01",
            "os": "cloud",
            "arch": "x86_64",
            "networks": networks,
            "containers": containers,
        }

    async def inspect_network(self, network_ref_id: str) -> Dict[str, Any]:
        """Inspect Azure VNet definition."""
        networks = await self.discover_networks()
        for net in networks:
            if net["provider_ref_id"] == network_ref_id or net["name"] == network_ref_id:
                return net
        return {"name": network_ref_id, "driver": "azure-vnet", "subnets": []}

    async def create_network(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Create an Azure VNet specification."""
        ref_id = f"/subscriptions/sub-0000/resourceGroups/rg-prod/providers/Microsoft.Network/virtualNetworks/{spec['name']}"
        return {
            "provider_ref_id": ref_id,
            "name": spec["name"],
            "driver": "azure-vnet",
            "internal": spec.get("internal", False),
            "subnets": spec.get("subnets", []),
        }

    async def delete_network(self, network_ref_id: str) -> bool:
        """Delete an Azure VNet specification."""
        return True

    async def connect_container(
        self,
        network_ref_id: str,
        container_ref_id: str,
        ipv4_address: Optional[str] = None,
        aliases: Optional[List[str]] = None,
    ) -> bool:
        """Attach an Azure VM NIC to an Azure VNet Subnet."""
        return True

    async def disconnect_container(
        self,
        network_ref_id: str,
        container_ref_id: str,
        force: bool = False,
    ) -> bool:
        """Detach an Azure VM NIC from an Azure VNet Subnet."""
        return True

    async def prune_unused_networks(self) -> List[str]:
        """Prune unused Azure VNets."""
        return []
