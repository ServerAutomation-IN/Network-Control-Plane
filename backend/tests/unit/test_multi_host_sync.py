"""Unit Tests for Multi-Host Fleet Sync and Aggregation — Network Control Plane"""

import pytest
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.host import InfrastructureHost
from app.models.network import Network, NetworkSubnet
from app.models.container import Container, ContainerNetwork
from app.services.inventory import InventoryService
from app.services.fleet_aggregator import FleetAggregatorService


@pytest.mark.asyncio
async def test_multi_host_sync_inventory_aggregation(db_session: AsyncSession):
    """Test multi-host synchronization and inventory aggregation across 3 host nodes."""
    now = datetime.now(timezone.utc)

    # 1. Register Host Alpha (Production)
    h_alpha = InfrastructureHost(
        id="host-node-alpha",
        name="Node Alpha",
        endpoint="tcp://10.0.1.10:2376",
        provider_type="docker",
        environment="production",
        status="ONLINE",
        created_at=now,
        last_seen=now,
    )
    # 2. Register Host Beta (Staging)
    h_beta = InfrastructureHost(
        id="host-node-beta",
        name="Node Beta",
        endpoint="tcp://10.0.1.11:2376",
        provider_type="docker",
        environment="staging",
        status="ONLINE",
        created_at=now,
        last_seen=now,
    )
    # 3. Register Host Gamma (Edge)
    h_gamma = InfrastructureHost(
        id="host-node-gamma",
        name="Node Gamma",
        endpoint="tcp://10.0.2.20:2376",
        provider_type="docker",
        environment="edge",
        status="UNREACHABLE",
        created_at=now,
        last_seen=now,
    )
    db_session.add_all([h_alpha, h_beta, h_gamma])
    await db_session.flush()

    # Create Networks for Alpha & Beta
    net_alpha = Network(
        id="net-alpha-overlay",
        host_id=h_alpha.id,
        provider_ref_id="ref-net-a",
        name="global_overlay",
        driver="overlay",
        scope="swarm",
    )
    net_beta = Network(
        id="net-beta-bridge",
        host_id=h_beta.id,
        provider_ref_id="ref-net-b",
        name="local_bridge",
        driver="bridge",
        scope="local",
    )
    db_session.add_all([net_alpha, net_beta])
    await db_session.flush()

    # Create Containers for Alpha & Beta
    cnt_alpha = Container(
        id="cnt-alpha-web",
        host_id=h_alpha.id,
        provider_ref_id="ref-cnt-a",
        name="frontend_app",
        image="nginx:alpine",
        status="running",
    )
    cnt_beta = Container(
        id="cnt-beta-db",
        host_id=h_beta.id,
        provider_ref_id="ref-cnt-b",
        name="postgres_db",
        image="postgres:15",
        status="running",
    )
    db_session.add_all([cnt_alpha, cnt_beta])
    await db_session.commit()

    # Evaluate Fleet Aggregation
    aggregator = FleetAggregatorService(db_session)
    summary = await aggregator.get_fleet_summary()

    assert summary["total_hosts"] == 3
    assert summary["healthy_hosts"] == 2
    assert summary["unreachable_hosts"] == 1
    assert summary["total_networks"] == 2
    assert summary["total_containers"] == 2
    assert summary["environment_distribution"]["production"] == 1
    assert summary["environment_distribution"]["staging"] == 1
    assert summary["environment_distribution"]["edge"] == 1
    assert summary["driver_distribution"]["overlay"] == 1
    assert summary["driver_distribution"]["bridge"] == 1
