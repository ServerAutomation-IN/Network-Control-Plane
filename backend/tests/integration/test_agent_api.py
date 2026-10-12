"""Integration Tests for Agent Protocol REST Endpoints — Network Control Plane"""

import pytest
from httpx import AsyncClient
from unittest.mock import patch


@pytest.mark.asyncio
async def test_agent_health_endpoint(async_client: AsyncClient):
    """Test GET /api/v1/agent/health returns 200 OK probe status."""
    response = await async_client.get("/api/v1/agent/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_agent_heartbeat_endpoint(async_client: AsyncClient):
    """Test POST /api/v1/agent/heartbeat processes heartbeat and auto-registers host."""
    payload = {
        "host_id": "agent-host-001",
        "agent_version": "1.0.0",
        "status": "HEALTHY",
        "uptime_seconds": 3600.5,
        "cpu_utilization_pct": 14.2,
        "memory_utilization_pct": 32.1,
    }

    response = await async_client.post("/api/v1/agent/heartbeat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["acknowledged"] is True
    assert data["next_heartbeat_interval_seconds"] == 15

    # Verify host auto-registered via GET /api/v1/hosts/{id}
    host_resp = await async_client.get("/api/v1/hosts/agent-host-001")
    assert host_resp.status_code == 200
    host_data = host_resp.json()
    assert host_data["id"] == "agent-host-001"
    assert host_data["status"] == "HEALTHY"


@pytest.mark.asyncio
async def test_agent_snapshot_endpoint(async_client: AsyncClient):
    """Test POST /api/v1/agent/snapshot ingests inventory snapshot."""
    payload = {
        "host_id": "agent-host-002",
        "host_info": {
            "hostname": "fleet-node-02.internal",
            "provider_type": "docker",
            "docker_version": "24.0.7",
            "os": "Debian 12",
            "architecture": "x86_64",
            "environment": "staging",
        },
        "networks": [
            {
                "provider_ref_id": "net-stage-01",
                "name": "staging_net",
                "driver": "bridge",
                "subnets": [{"subnet": "172.30.0.0/16", "gateway": "172.30.0.1"}],
            }
        ],
        "containers": [
            {
                "provider_ref_id": "cnt-stage-01",
                "name": "redis_cache",
                "image": "redis:7-alpine",
                "status": "running",
                "attachments": [
                    {
                        "network_name": "staging_net",
                        "network_ref_id": "net-stage-01",
                        "ip_address": "172.30.0.5",
                    }
                ],
            }
        ],
    }

    response = await async_client.post("/api/v1/agent/snapshot", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "ingested successfully" in data["message"]
    assert data["data"]["host_id"] == "agent-host-002"

    # Verify host record updated
    host_resp = await async_client.get("/api/v1/hosts/agent-host-002")
    assert host_resp.status_code == 200
    host_data = host_resp.json()
    assert host_data["name"] == "fleet-node-02.internal"
    assert host_data["status"] == "ONLINE"


@pytest.mark.asyncio
async def test_agent_events_endpoint(async_client: AsyncClient):
    """Test POST /api/v1/agent/events logs agent runtime events."""
    payload = {
        "host_id": "agent-host-001",
        "event_type": "network.create",
        "resource_type": "network",
        "resource_id": "net-stage-01",
        "attributes": {"driver": "bridge", "name": "staging_net"},
    }

    response = await async_client.post("/api/v1/agent/events", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["event_type"] == "network.create"


@pytest.mark.asyncio
async def test_agent_api_authentication(async_client: AsyncClient):
    """Test API token authentication enforcement for Agent Protocol when AGENT_API_TOKEN is set."""
    payload = {
        "host_id": "secure-host-01",
        "agent_version": "1.0.0",
        "status": "HEALTHY",
    }

    with patch("app.api.v1.agent.settings.AGENT_API_TOKEN", "secret-agent-token-99"):
        # 1. Unauthenticated request should fail 401
        unauth_resp = await async_client.post("/api/v1/agent/heartbeat", json=payload)
        assert unauth_resp.status_code == 401

        # 2. Invalid token request should fail 401
        bad_token_resp = await async_client.post(
            "/api/v1/agent/heartbeat",
            json=payload,
            headers={"Authorization": "Bearer wrong-token"},
        )
        assert bad_token_resp.status_code == 401

        # 3. Valid token request should succeed 200
        valid_resp = await async_client.post(
            "/api/v1/agent/heartbeat",
            json=payload,
            headers={"Authorization": "Bearer secret-agent-token-99"},
        )
        assert valid_resp.status_code == 200
        assert valid_resp.json()["acknowledged"] is True
