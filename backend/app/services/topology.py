"""Topology Service — Network Control Plane

Builds node/edge graph representations of managed infrastructure hosts, virtual networks, and container workloads.
"""

from typing import List, Dict, Any
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.host import InfrastructureHost
from app.models.network import Network
from app.models.container import Container
from app.schemas.topology import TopologyResponse, TopologyNode, TopologyEdge, NodeData


class TopologyService:
    """Constructs topology graph data structures for frontend React Flow visualizers."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_topology_graph(
        self,
        host_id: str | None = None,
        environment: str | None = None,
    ) -> TopologyResponse:
        """Query inventory entities and return node/edge topology payload with host grouping bounds."""
        # 1. Fetch Hosts
        hosts_stmt = select(InfrastructureHost)
        if host_id:
            hosts_stmt = hosts_stmt.where(InfrastructureHost.id == host_id)
        if environment:
            hosts_stmt = hosts_stmt.where(InfrastructureHost.environment == environment)
        hosts = (await self.db.execute(hosts_stmt)).scalars().all()
        target_host_ids = {h.id for h in hosts}

        # 2. Fetch Networks with Subnets
        nets_stmt = select(Network).options(selectinload(Network.subnets))
        if host_id or environment:
            nets_stmt = nets_stmt.where(Network.host_id.in_(target_host_ids))
        networks = (await self.db.execute(nets_stmt)).scalars().all()

        # 3. Fetch Containers with Attachments
        cnts_stmt = select(Container).options(
            selectinload(Container.network_attachments)
        )
        if host_id or environment:
            cnts_stmt = cnts_stmt.where(Container.host_id.in_(target_host_ids))
        containers = (await self.db.execute(cnts_stmt)).scalars().all()

        nodes: List[TopologyNode] = []
        edges: List[TopologyEdge] = []

        # Map Host Grouping Nodes
        for host in hosts:
            nodes.append(
                TopologyNode(
                    id=f"host-{host.id}",
                    type="hostGroupNode",
                    data=NodeData(
                        label=host.name,
                        sublabel=host.endpoint,
                        status=host.status,
                        environment=host.environment,
                        host_id=host.id,
                        attributes={"docker_version": host.docker_version, "os": host.os},
                    ),
                )
            )

        # Map Network Nodes & Host-to-Network Edges
        for net in networks:
            subnets_data = [
                {"subnet": s.subnet, "gateway": s.gateway} for s in net.subnets
            ]
            nodes.append(
                TopologyNode(
                    id=f"net-{net.id}",
                    type="networkNode",
                    data=NodeData(
                        label=net.name,
                        driver=net.driver,
                        scope=net.scope,
                        host_id=net.host_id,
                        subnets=subnets_data,
                        attributes={"internal": net.internal, "attachable": net.attachable},
                    ),
                )
            )
            # Edge from host to network
            edges.append(
                TopologyEdge(
                    id=f"edge-host-{net.host_id}-net-{net.id}",
                    source=f"host-{net.host_id}",
                    target=f"net-{net.id}",
                    label="hosts",
                    animated=False,
                )
            )

        # Map Container Nodes & Container-to-Network Edges
        for cnt in containers:
            primary_ip = None
            if cnt.network_attachments and len(cnt.network_attachments) > 0:
                primary_ip = cnt.network_attachments[0].ip_address

            nodes.append(
                TopologyNode(
                    id=f"cnt-{cnt.id}",
                    type="containerNode",
                    data=NodeData(
                        label=cnt.name,
                        sublabel=cnt.image or "workload",
                        status=cnt.status,
                        host_id=cnt.host_id,
                        ip_address=primary_ip,
                        attributes={"labels": cnt.labels},
                    ),
                )
            )

            for att in cnt.network_attachments:
                edges.append(
                    TopologyEdge(
                        id=f"edge-net-{att.network_id}-cnt-{cnt.id}",
                        source=f"net-{att.network_id}",
                        target=f"cnt-{cnt.id}",
                        label=att.ip_address or "attached",
                        animated=cnt.status == "running",
                        style={"stroke": "#2563eb" if cnt.status == "running" else "#94a3b8"},
                    )
                )

        node_ids = {n.id for n in nodes}
        filtered_edges = [
            e for e in edges if e.source in node_ids and e.target in node_ids
        ]

        stats = {
            "hosts_count": len(hosts),
            "networks_count": len(networks),
            "containers_count": len(containers),
            "edges_count": len(filtered_edges),
        }

        return TopologyResponse(nodes=nodes, edges=filtered_edges, stats=stats)
