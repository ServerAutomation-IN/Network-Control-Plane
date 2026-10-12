"""Integration Tests for Network Operations & Audit APIs — Network Control Plane"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.host import InfrastructureHost
from app.models.network import Network


@pytest.mark.asyncio
async def test_audit_api_empty_list(async_client: AsyncClient):
    """Test GET /api/v1/audit returns list of audit events."""
    res = await async_client.get("/api/v1/audit")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


@pytest.mark.asyncio
async def test_jobs_api_empty_list(async_client: AsyncClient):
    """Test GET /api/v1/jobs returns list of background jobs."""
    res = await async_client.get("/api/v1/jobs")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


@pytest.mark.asyncio
async def test_network_safety_check_api(async_client: AsyncClient, db_session: AsyncSession):
    """Test GET /api/v1/networks/{id}/safety-check endpoint."""
    host = InfrastructureHost(
        id="host-test-1",
        name="Test Host",
        endpoint="unix:///var/run/docker.sock",
    )
    net = Network(
        id="net-safety-1",
        host_id="host-test-1",
        provider_ref_id="raw-net-1",
        name="my_test_network",
        driver="bridge",
    )
    db_session.add(host)
    db_session.add(net)
    await db_session.commit()

    res = await async_client.get(f"/api/v1/networks/{net.id}/safety-check")
    assert res.status_code == 200
    data = res.json()
    assert data["network_id"] == net.id
    assert data["network_name"] == "my_test_network"
    assert data["is_safe_to_delete"] is True
    assert data["risk_level"] == "LOW"
