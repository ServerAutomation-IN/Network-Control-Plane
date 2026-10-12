"""Fleet Inventory Aggregator Service — Network Control Plane

Aggregates workload inventory metrics, network counts, driver distributions, and container states across all active hosts.
"""

from typing import Dict, Any, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.host import InfrastructureHost
from app.models.network import Network, NetworkSubnet
from app.models.container import Container


class FleetAggregatorService:
    """Service providing multi-host fleet inventory aggregation metrics."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_fleet_summary(self) -> Dict[str, Any]:
        """Aggregate high-level fleet statistics across all registered hosts."""
        # 1. Hosts metrics
        hosts_stmt = select(InfrastructureHost)
        hosts = (await self.db.execute(hosts_stmt)).scalars().all()
        
        total_hosts = len(hosts)
        healthy_hosts = sum(1 for h in hosts if h.status in ("HEALTHY", "ONLINE"))
        unreachable_hosts = sum(1 for h in hosts if h.status in ("UNREACHABLE", "OFFLINE"))

        environment_distribution: Dict[str, int] = {}
        for h in hosts:
            env = h.environment or "development"
            environment_distribution[env] = environment_distribution.get(env, 0) + 1

        # 2. Networks & Driver distribution
        nets_stmt = select(Network)
        networks = (await self.db.execute(nets_stmt)).scalars().all()
        total_networks = len(networks)

        driver_distribution: Dict[str, int] = {}
        for n in networks:
            driver = n.driver or "bridge"
            driver_distribution[driver] = driver_distribution.get(driver, 0) + 1

        # 3. Subnets count
        subnets_count_stmt = select(func.count(NetworkSubnet.id))
        total_subnets = (await self.db.execute(subnets_count_stmt)).scalar() or 0

        # 4. Containers & Status distribution
        cnts_stmt = select(Container)
        containers = (await self.db.execute(cnts_stmt)).scalars().all()
        total_containers = len(containers)

        running_containers = sum(1 for c in containers if c.status == "running")
        stopped_containers = sum(1 for c in containers if c.status in ("exited", "stopped"))

        return {
            "total_hosts": total_hosts,
            "healthy_hosts": healthy_hosts,
            "unreachable_hosts": unreachable_hosts,
            "total_networks": total_networks,
            "total_subnets": total_subnets,
            "total_containers": total_containers,
            "running_containers": running_containers,
            "stopped_containers": stopped_containers,
            "environment_distribution": environment_distribution,
            "driver_distribution": driver_distribution,
        }
