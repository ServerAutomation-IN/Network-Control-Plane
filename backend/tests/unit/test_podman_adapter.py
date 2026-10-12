"""Unit Tests for Podman Provider Adapter — Network Control Plane"""

import pytest
from app.podman.adapter import PodmanAdapter


@pytest.mark.asyncio
async def test_podman_adapter_discovery():
    """Test PodmanAdapter ping, network discovery, and container normalization."""
    adapter = PodmanAdapter()

    assert await adapter.ping() is True

    snapshot = await adapter.discover()
    assert snapshot["provider"] == "podman"
    assert "networks" in snapshot
    assert "containers" in snapshot

    networks = await adapter.discover_networks()
    assert len(networks) >= 1
    assert networks[0]["name"] == "podman"
    assert networks[0]["driver"] == "bridge"

    containers = await adapter.discover_containers()
    assert len(containers) >= 1
    assert containers[0]["name"] == "podman_web_app"
    assert len(containers[0]["attachments"]) >= 1


@pytest.mark.asyncio
async def test_podman_adapter_mutations():
    """Test PodmanAdapter lifecycle operations (create, connect, disconnect, delete)."""
    adapter = PodmanAdapter()

    spec = {"name": "test_podman_net", "driver": "bridge"}
    created_net = await adapter.create_network(spec)
    assert created_net["name"] == "test_podman_net"

    assert await adapter.connect_container("podman-net-podman", "podman-cnt-app-1", ipv4_address="10.88.0.50") is True
    assert await adapter.disconnect_container("podman-net-podman", "podman-cnt-app-1") is True
    assert await adapter.delete_network("podman-net-test") is True
