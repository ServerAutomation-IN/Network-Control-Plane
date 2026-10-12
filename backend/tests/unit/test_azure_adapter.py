"""Unit Tests for Azure VNet Provider Adapter — Network Control Plane"""

import pytest
from app.cloud.azure.adapter import AzureAdapter


@pytest.mark.asyncio
async def test_azure_adapter_discovery():
    """Test AzureAdapter discovery of Azure VNet networks and VM NIC workloads."""
    adapter = AzureAdapter(subscription_id="sub-0000")

    assert await adapter.ping() is True

    snapshot = await adapter.discover()
    assert snapshot["provider"] == "azure"
    assert snapshot["endpoint"] == "sub-0000"
    assert "networks" in snapshot
    assert "containers" in snapshot

    networks = await adapter.discover_networks()
    assert len(networks) >= 1
    assert networks[0]["name"] == "azure-prod-vnet"
    assert networks[0]["driver"] == "azure-vnet"

    containers = await adapter.discover_containers()
    assert len(containers) >= 1
    assert containers[0]["name"] == "azure-vm-frontend"
    assert "vm_size" in containers[0]["labels"]


@pytest.mark.asyncio
async def test_azure_adapter_mutations():
    """Test AzureAdapter network lifecycle and NIC attachment operations."""
    adapter = AzureAdapter()

    spec = {"name": "azure-dev-vnet", "driver": "azure-vnet"}
    created_net = await adapter.create_network(spec)
    assert created_net["name"] == "azure-dev-vnet"
    assert "azure-dev-vnet" in created_net["provider_ref_id"]

    assert await adapter.connect_container("azure-prod-vnet", "azure-vm-frontend") is True
    assert await adapter.disconnect_container("azure-prod-vnet", "azure-vm-frontend") is True
    assert await adapter.delete_network("azure-prod-vnet") is True
