"""Unit Tests for Topology Service — Network Control Plane"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.host import InfrastructureHost
from app.models.network import Network, NetworkSubnet
from app.models.container import Container, ContainerNetwork
from app.services.topology import TopologyService


@pytest.mark.asyncio
async def test_topology_graph_builder(db_session: AsyncSession):
    """Test topology service constructs host, network, container nodes and edges."""
    host = InfrastructureHost(id="host-1", name="Primary Host", endpoint="unix:///var/run/docker.sock")
    net = Network(id="net-1", host_id="host-1", provider_ref_id="raw-net-1", name="app_net", driver="bridge")
    sub = NetworkSubnet(id="sub-1", network_id="net-1", subnet="172.22.0.0/16", gateway="172.22.0.1")
    cnt = Container(id="cnt-1", host_id="host-1", provider_ref_id="raw-cnt-1", name="web_server", status="running")
    att = ContainerNetwork(id="att-1", container_id="cnt-1", network_id="net-1", ip_address="172.22.0.5")

    db_session.add_all([host, net, sub, cnt, att])
    await db_session.commit()

    service = TopologyService(db_session)
    topo = await service.get_topology_graph()

    assert topo.stats["hosts_count"] == 1
    assert topo.stats["networks_count"] == 1
    assert topo.stats["containers_count"] == 1

    node_ids = {n.id for n in topo.nodes}
    assert "host-host-1" in node_ids
    assert "net-net-1" in node_ids
    assert "cnt-cnt-1" in node_ids

    edge_sources = {e.source for e in topo.edges}
    assert "host-host-1" in edge_sources
    assert "net-net-1" in edge_sources
