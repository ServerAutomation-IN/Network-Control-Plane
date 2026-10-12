"""Unit Tests for Kubernetes / OpenShift Provider Adapter — Network Control Plane"""

import pytest
from app.kubernetes.adapter import KubernetesAdapter


@pytest.mark.asyncio
async def test_kubernetes_adapter_discovery():
    """Test KubernetesAdapter discovery of OpenShift CNI networks and pod containers."""
    adapter = KubernetesAdapter()

    assert await adapter.ping() is True

    snapshot = await adapter.discover()
    assert snapshot["provider"] == "openshift"
    assert "networks" in snapshot
    assert "containers" in snapshot

    networks = await adapter.discover_networks()
    assert len(networks) >= 1
    assert networks[0]["name"] == "default-pod-network"
    assert networks[0]["driver"] == "ovn-kubernetes"

    containers = await adapter.discover_containers()
    assert len(containers) >= 1
    assert containers[0]["name"] == "openshift-frontend-api"
    assert "namespace" in containers[0]["labels"]


@pytest.mark.asyncio
async def test_kubernetes_adapter_mutations():
    """Test KubernetesAdapter lifecycle resource operations."""
    adapter = KubernetesAdapter()

    spec = {"name": "crd-macvlan-net", "driver": "macvlan"}
    created_net = await adapter.create_network(spec)
    assert created_net["name"] == "crd-macvlan-net"

    assert await adapter.connect_container("k8s-net-default", "k8s-pod-frontend-api-01") is True
    assert await adapter.disconnect_container("k8s-net-default", "k8s-pod-frontend-api-01") is True
    assert await adapter.delete_network("k8s-net-default") is True
