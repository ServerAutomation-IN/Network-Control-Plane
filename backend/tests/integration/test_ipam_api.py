"""Integration Tests for IPAM REST APIs — Network Control Plane"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.host import InfrastructureHost
from app.models.network import Network, NetworkSubnet


@pytest.mark.asyncio
async def test_ipam_subnets_api(async_client: AsyncClient, db_session: AsyncSession):
    """Test GET /api/v1/ipam/subnets endpoint returns subnet list with utilization."""
    host = InfrastructureHost(id="host-ipam-1", name="IPAM Host", endpoint="unix:///var/run/docker.sock")
    net = Network(id="net-ipam-1", host_id="host-ipam-1", provider_ref_id="ref-ipam-1", name="ipam_net", driver="bridge")
    sub = NetworkSubnet(id="sub-ipam-1", network_id="net-ipam-1", subnet="172.30.0.0/16", gateway="172.30.0.1")
    db_session.add_all([host, net, sub])
    await db_session.commit()

    res = await async_client.get("/api/v1/ipam/subnets")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 1
    found = next((s for s in data if s["subnet"] == "172.30.0.0/16"), None)
    assert found is not None
    assert found["network_name"] == "ipam_net"
    assert found["total_ips"] == 65536


@pytest.mark.asyncio
async def test_ipam_conflicts_detection_api(async_client: AsyncClient, db_session: AsyncSession):
    """Test GET /api/v1/ipam/conflicts identifies overlapping subnets."""
    host = InfrastructureHost(id="host-ipam-2", name="IPAM Conflict Host", endpoint="unix:///var/run/docker.sock")
    net1 = Network(id="net-c1", host_id="host-ipam-2", provider_ref_id="ref-c1", name="net_alpha", driver="bridge")
    sub1 = NetworkSubnet(id="sub-c1", network_id="net-c1", subnet="10.50.0.0/16")

    net2 = Network(id="net-c2", host_id="host-ipam-2", provider_ref_id="ref-c2", name="net_beta", driver="bridge")
    sub2 = NetworkSubnet(id="sub-c2", network_id="net-c2", subnet="10.50.4.0/24")

    db_session.add_all([host, net1, sub1, net2, sub2])
    await db_session.commit()

    res = await async_client.get("/api/v1/ipam/conflicts")
    assert res.status_code == 200
    conflicts = res.json()
    assert len(conflicts) >= 1
    found = next((c for c in conflicts if c["conflict_type"] == "OVERLAPPING_SUBNET"), None)
    assert found is not None
    assert "10.50.0.0/16" in found["description"]


@pytest.mark.asyncio
async def test_ipam_validate_api(async_client: AsyncClient):
    """Test POST /api/v1/ipam/validate endpoint."""
    payload = {"subnet": "192.168.10.0/24", "requested_ip": "192.168.10.50"}
    res = await async_client.post("/api/v1/ipam/validate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["is_valid"] is True
    assert data["is_ip_in_subnet"] is True
