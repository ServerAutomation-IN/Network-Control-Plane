"""Unit Tests for Fleet Inventory Aggregator Service — Network Control Plane"""

import pytest
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.host import InfrastructureHost
from app.models.network import Network
from app.models.container import Container
from app.services.fleet_aggregator import FleetAggregatorService


@pytest.mark.asyncio
async def test_fleet_aggregator_summary(db_session: AsyncSession):
    """Test FleetAggregatorService correctly aggregates counts and distributions across fleet."""
    now = datetime.now(timezone.utc)

    # 1. Seed Hosts
    h1 = InfrastructureHost(
        id="fleet-h1",
        name="Host 1",
        endpoint="unix:///var/run/docker.sock",
        environment="production",
        status="ONLINE",
        created_at=now,
        last_seen=now,
    )
    h2 = InfrastructureHost(
        id="fleet-h2",
        name="Host 2",
        endpoint="tcp://10.0.0.5:2375",
        environment="staging",
        status="UNREACHABLE",
        created_at=now,
        last_seen=now,
    )
    db_session.add_all([h1, h2])

    # 2. Seed Networks
    n1 = Network(
        id="net-f1",
        host_id="fleet-h1",
        provider_ref_id="p-n1",
        name="overlay_net",
        driver="overlay",
    )
    n2 = Network(
        id="net-f2",
        host_id="fleet-h1",
        provider_ref_id="p-n2",
        name="bridge_net",
        driver="bridge",
    )
    db_session.add_all([n1, n2])

    # 3. Seed Container
    c1 = Container(
        id="cnt-f1",
        host_id="fleet-h1",
        provider_ref_id="p-c1",
        name="app_worker",
        image="python:3.11",
        status="running",
    )
    db_session.add(c1)
    await db_session.commit()

    aggregator = FleetAggregatorService(db_session)
    summary = await aggregator.get_fleet_summary()

    assert summary["total_hosts"] >= 2
    assert summary["healthy_hosts"] >= 1
    assert summary["unreachable_hosts"] >= 1
    assert summary["total_networks"] >= 2
    assert summary["total_containers"] >= 1
    assert summary["driver_distribution"].get("overlay") >= 1
    assert summary["environment_distribution"].get("production") >= 1
