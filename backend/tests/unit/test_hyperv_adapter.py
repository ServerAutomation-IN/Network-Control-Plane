"""Unit Tests for Microsoft Hyper-V / SCVMM Provider Adapter — Network Control Plane"""

import pytest
from app.cloud.hyperv.adapter import HyperVAdapter


@pytest.mark.asyncio
async def test_hyperv_adapter_discovery():
    """Test HyperVAdapter discovery of Hyper-V Virtual Switches / VM Networks and VM NIC workloads."""
    adapter = HyperVAdapter(hyperv_host="hyperv-host-01.corp.internal")

    assert await adapter.ping() is True

    snapshot = await adapter.discover()
    assert snapshot["provider"] == "hyperv"
    assert snapshot["endpoint"] == "hyperv-host-01.corp.internal"
    assert "networks" in snapshot
    assert "containers" in snapshot

    networks = await adapter.discover_networks()
    assert len(networks) >= 1
    assert networks[0]["name"] == "HyperV-External-vSwitch"
    assert networks[0]["driver"] == "hyperv-vswitch"

    containers = await adapter.discover_containers()
    assert len(containers) >= 1
    assert containers[0]["name"] == "hyperv-win-server-2022"
    assert "generation" in containers[0]["labels"]


@pytest.mark.asyncio
async def test_hyperv_adapter_mutations():
    """Test HyperVAdapter network lifecycle and vNIC attachment operations."""
    adapter = HyperVAdapter()

    spec = {"name": "hv-dev-vswitch", "driver": "hyperv-vswitch"}
    created_net = await adapter.create_network(spec)
    assert created_net["name"] == "hv-dev-vswitch"
    assert created_net["provider_ref_id"] == "hyperv-vswitch-hv-dev-vswitch"

    assert await adapter.connect_container("HyperV-External-vSwitch", "hyperv-win-server-2022") is True
    assert await adapter.disconnect_container("HyperV-External-vSwitch", "hyperv-win-server-2022") is True
    assert await adapter.delete_network("HyperV-External-vSwitch") is True
