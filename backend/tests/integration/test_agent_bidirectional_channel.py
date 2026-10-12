"""Integration Tests for Agent Bidirectional Command Channel — Network Control Plane"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_agent_command_lifecycle_integration(async_client: AsyncClient):
    """Test full command lifecycle: enqueue -> poll -> execute -> result submission."""
    host_id = "agent-host-integration-01"

    # 1. Enqueue command via POST /api/v1/agent/commands
    enqueue_payload = {
        "command_id": "auto",
        "host_id": host_id,
        "action": "CREATE_NETWORK",
        "payload": {
            "name": "isolated_tenant_net",
            "driver": "bridge",
            "internal": True,
        },
        "timeout_seconds": 30,
    }
    enqueue_resp = await async_client.post("/api/v1/agent/commands", json=enqueue_payload)
    assert enqueue_resp.status_code == 200
    enqueue_data = enqueue_resp.json()
    assert enqueue_data["status"] == "success"
    command_id = enqueue_data["data"]["command_id"]
    assert command_id.startswith("cmd-")

    # 2. Agent polls for pending commands via GET /api/v1/agent/commands?host_id=...
    poll_resp = await async_client.get(f"/api/v1/agent/commands?host_id={host_id}")
    assert poll_resp.status_code == 200
    poll_data = poll_resp.json()
    assert poll_data["status"] == "success"
    commands = poll_data["data"]
    assert len(commands) == 1
    assert commands[0]["command_id"] == command_id
    assert commands[0]["action"] == "CREATE_NETWORK"
    assert commands[0]["payload"]["name"] == "isolated_tenant_net"

    # 3. Subsequent poll returns 0 commands because status is now DISPATCHED
    re_poll_resp = await async_client.get(f"/api/v1/agent/commands?host_id={host_id}")
    assert re_poll_resp.status_code == 200
    assert len(re_poll_resp.json()["data"]) == 0

    # 4. Agent reports execution result via POST /api/v1/agent/commands/{command_id}/result
    result_payload = {
        "command_id": command_id,
        "host_id": host_id,
        "success": True,
        "result_data": {
            "provider_ref_id": "docker-net-uuid-9999",
            "name": "isolated_tenant_net",
        },
    }
    result_resp = await async_client.post(
        f"/api/v1/agent/commands/{command_id}/result",
        json=result_payload,
    )
    assert result_resp.status_code == 200
    result_data = result_resp.json()
    assert result_data["status"] == "success"
    assert result_data["data"]["status"] == "COMPLETED"
    assert result_data["data"]["success"] is True


@pytest.mark.asyncio
async def test_agent_command_result_not_found(async_client: AsyncClient):
    """Test reporting result for non-existent command returns 404 Not Found."""
    result_payload = {
        "command_id": "non-existent-cmd",
        "host_id": "host-test",
        "success": True,
    }
    resp = await async_client.post(
        "/api/v1/agent/commands/non-existent-cmd/result",
        json=result_payload,
    )
    assert resp.status_code == 404
