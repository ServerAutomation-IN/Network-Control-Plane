"""Unit Tests for GCP Cloud VPC Provider Adapter — Network Control Plane"""

import pytest
from app.cloud.gcp.adapter import GCPAdapter


@pytest.mark.asyncio
async def test_gcp_adapter_discovery():
    """Test GCPAdapter discovery of GCP VPC networks and GCE NIC workloads."""
    adapter = GCPAdapter(project_id="corp-net-prod")

    assert await adapter.ping() is True

    snapshot = await adapter.discover()
    assert snapshot["provider"] == "gcp"
    assert snapshot["endpoint"] == "corp-net-prod"
    assert "networks" in snapshot
    assert "containers" in snapshot

    networks = await adapter.discover_networks()
    assert len(networks) >= 1
    assert networks[0]["name"] == "gcp-prod-vpc"
    assert networks[0]["driver"] == "gcp-vpc"

    containers = await adapter.discover_containers()
    assert len(containers) >= 1
    assert containers[0]["name"] == "gce-app-instance"
    assert "machine_type" in containers[0]["labels"]


@pytest.mark.asyncio
async def test_gcp_adapter_mutations():
    """Test GCPAdapter network lifecycle and GCE NIC attachment operations."""
    adapter = GCPAdapter()

    spec = {"name": "gcp-dev-vpc", "driver": "gcp-vpc"}
    created_net = await adapter.create_network(spec)
    assert created_net["name"] == "gcp-dev-vpc"
    assert "gcp-dev-vpc" in created_net["provider_ref_id"]

    assert await adapter.connect_container("gcp-prod-vpc", "gce-app-instance") is True
    assert await adapter.disconnect_container("gcp-prod-vpc", "gce-app-instance") is True
    assert await adapter.delete_network("gcp-prod-vpc") is True
