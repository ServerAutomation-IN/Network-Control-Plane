"""Unit Tests for VMware vSphere / NSX Provider Adapter — Network Control Plane"""

import pytest
from app.cloud.vmware.adapter import VMwareAdapter


@pytest.mark.asyncio
async def test_vmware_adapter_discovery():
    """Test VMwareAdapter discovery of vSphere port groups / NSX segments and VM vNICs."""
    adapter = VMwareAdapter(vcenter_host="vcenter.corp.internal")

    assert await adapter.ping() is True

    snapshot = await adapter.discover()
    assert snapshot["provider"] == "vmware"
    assert snapshot["endpoint"] == "vcenter.corp.internal"
    assert "networks" in snapshot
    assert "containers" in snapshot

    networks = await adapter.discover_networks()
    assert len(networks) >= 1
    assert networks[0]["name"] == "vDS-Production-PortGroup"
    assert networks[0]["driver"] == "vsphere-vds"

    containers = await adapter.discover_containers()
    assert len(containers) >= 1
    assert containers[0]["name"] == "vsphere-vm-app-01"
    assert "guest_os" in containers[0]["labels"]


@pytest.mark.asyncio
async def test_vmware_adapter_mutations():
    """Test VMwareAdapter network lifecycle and vNIC attachment operations."""
    adapter = VMwareAdapter()

    spec = {"name": "dpg-dev-v200", "driver": "vsphere-vds"}
    created_net = await adapter.create_network(spec)
    assert created_net["name"] == "dpg-dev-v200"
    assert created_net["provider_ref_id"] == "dvportgroup-dpg-dev-v200"

    assert await adapter.connect_container("vDS-Production-PortGroup", "vsphere-vm-app-01") is True
    assert await adapter.disconnect_container("vDS-Production-PortGroup", "vsphere-vm-app-01") is True
    assert await adapter.delete_network("vDS-Production-PortGroup") is True
