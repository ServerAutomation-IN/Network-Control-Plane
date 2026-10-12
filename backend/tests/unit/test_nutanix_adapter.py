"""Unit Tests for Nutanix AHV Provider Adapter — Network Control Plane"""

import pytest
from app.cloud.nutanix.adapter import NutanixAdapter


@pytest.mark.asyncio
async def test_nutanix_adapter_discovery():
    """Test NutanixAdapter discovery of AHV networks/subnets and VM vNICs."""
    adapter = NutanixAdapter(prism_host="prism.corp.internal")

    assert await adapter.ping() is True

    snapshot = await adapter.discover()
    assert snapshot["provider"] == "nutanix"
    assert snapshot["endpoint"] == "prism.corp.internal"
    assert "networks" in snapshot
    assert "containers" in snapshot

    networks = await adapter.discover_networks()
    assert len(networks) >= 1
    assert networks[0]["name"] == "nutanix-ahv-prod-vlan"
    assert networks[0]["driver"] == "nutanix-ahv"

    containers = await adapter.discover_containers()
    assert len(containers) >= 1
    assert containers[0]["name"] == "nutanix-ahv-analytics-vm"
    assert "vcpus" in containers[0]["labels"]


@pytest.mark.asyncio
async def test_nutanix_adapter_mutations():
    """Test NutanixAdapter network lifecycle and vNIC attachment operations."""
    adapter = NutanixAdapter()

    spec = {"name": "ahv-vlan-20-dev", "driver": "nutanix-ahv"}
    created_net = await adapter.create_network(spec)
    assert created_net["name"] == "ahv-vlan-20-dev"
    assert created_net["provider_ref_id"] == "nutanix-vnet-ahv-vlan-20-dev"

    assert await adapter.connect_container("nutanix-ahv-prod-vlan", "nutanix-ahv-analytics-vm") is True
    assert await adapter.disconnect_container("nutanix-ahv-prod-vlan", "nutanix-ahv-analytics-vm") is True
    assert await adapter.delete_network("nutanix-ahv-prod-vlan") is True
