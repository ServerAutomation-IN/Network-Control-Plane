"""Unit Tests for Fleet Host Health Monitoring Worker — Network Control Plane"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.host import InfrastructureHost
from app.services.fleet_health import FleetHealthWorker


@pytest.mark.asyncio
async def test_fleet_health_worker_evaluation(db_session: AsyncSession):
    """Test FleetHealthWorker identifies healthy vs stale/unreachable hosts."""
    now = datetime.now(timezone.utc)
    old_time = now - timedelta(seconds=120)

    # 1. Active Host
    active_host = InfrastructureHost(
        id="host-healthy-01",
        name="Active Host",
        endpoint="unix:///var/run/docker.sock",
        status="HEALTHY",
        last_seen=now,
        created_at=now,
    )
    # 2. Stale Host
    stale_host = InfrastructureHost(
        id="host-stale-02",
        name="Stale Host",
        endpoint="tcp://192.168.99.99:2375",
        status="HEALTHY",
        last_seen=old_time,
        created_at=old_time,
    )

    db_session.add_all([active_host, stale_host])
    await db_session.commit()

    with patch("app.services.fleet_health.DockerAdapter") as mock_adapter_cls:
        mock_adapter = MagicMock()
        mock_adapter.ping.side_effect = Exception("Unreachable")
        mock_adapter_cls.return_value = mock_adapter

        worker = FleetHealthWorker(db_session, timeout_seconds=30)
        report = await worker.evaluate_fleet_health()

        assert report["total_hosts"] >= 2
        assert report["unreachable_hosts"] >= 1

        # Refresh stale host and check status updated to UNREACHABLE
        await db_session.refresh(stale_host)
        assert stale_host.status == "UNREACHABLE"
