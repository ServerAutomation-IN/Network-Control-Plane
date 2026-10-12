"""Unit Tests for Host Agent Daemon — network-control-plane-agent"""

import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

# Add agent package directory to sys.path so we can import daemon
AGENT_DIR = Path(__file__).resolve().parent.parent.parent.parent / "agent" / "network-control-plane-agent"
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))

from daemon import HostAgentDaemon  # noqa: E402


@pytest.mark.asyncio
async def test_host_agent_daemon_heartbeat():
    """Test HostAgentDaemon constructs and sends heartbeat payload."""
    daemon = HostAgentDaemon(
        host_id="test-host-daemon-01",
        control_plane_url="http://localhost:8000",
        api_token="test-secret-token",
    )
    assert daemon.host_id == "test-host-daemon-01"
    headers = daemon.get_headers()
    assert headers["Authorization"] == "Bearer test-secret-token"

    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_client.post = AsyncMock(return_value=mock_resp)

    success = await daemon.send_heartbeat(mock_client)
    assert success is True
    assert mock_client.post.called


@pytest.mark.asyncio
async def test_host_agent_daemon_snapshot():
    """Test HostAgentDaemon sends snapshot payload."""
    daemon = HostAgentDaemon(
        host_id="test-host-daemon-01",
        control_plane_url="http://localhost:8000",
    )

    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_client.post = AsyncMock(return_value=mock_resp)

    success = await daemon.send_snapshot(mock_client)
    assert success is True
    assert mock_client.post.called


@pytest.mark.asyncio
async def test_host_agent_daemon_events():
    """Test HostAgentDaemon sends runtime events."""
    daemon = HostAgentDaemon(
        host_id="test-host-daemon-01",
        control_plane_url="http://localhost:8000",
    )

    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_client.post = AsyncMock(return_value=mock_resp)

    success = await daemon.send_event(
        mock_client,
        event_type="container.start",
        resource_type="container",
        resource_id="cnt-100",
        attributes={"image": "nginx"},
    )
    assert success is True
    assert mock_client.post.called


@pytest.mark.asyncio
async def test_host_agent_daemon_execute_ping():
    """Test HostAgentDaemon executes PING command without Docker requirement."""
    daemon = HostAgentDaemon(host_id="test-host-daemon-01")
    result = daemon.execute_docker_command("PING", {})
    assert result["pong"] is True
    assert result["host_id"] == "test-host-daemon-01"


@pytest.mark.asyncio
async def test_host_agent_daemon_poll_and_execute_commands():
    """Test HostAgentDaemon polls for commands, executes them, and posts results."""
    daemon = HostAgentDaemon(
        host_id="test-host-daemon-01",
        control_plane_url="http://localhost:8000",
    )

    mock_client = MagicMock()
    # Mock GET /api/v1/agent/commands
    poll_resp = MagicMock()
    poll_resp.status_code = 200
    poll_resp.json.return_value = {
        "status": "success",
        "data": [
            {
                "command_id": "cmd-test-101",
                "action": "PING",
                "payload": {},
            }
        ],
    }
    mock_client.get = AsyncMock(return_value=poll_resp)

    # Mock POST /api/v1/agent/commands/{id}/result
    result_resp = MagicMock()
    result_resp.status_code = 200
    mock_client.post = AsyncMock(return_value=result_resp)

    count = await daemon.poll_and_execute_commands(mock_client)
    assert count == 1
    assert mock_client.get.called
    assert mock_client.post.called


@pytest.mark.asyncio
async def test_host_agent_daemon_pluggable_collector_initialization():
    """Test HostAgentDaemon initializes specified runtime collector."""
    daemon_podman = HostAgentDaemon(host_id="host-podman-01", runtime="podman")
    assert daemon_podman.collector.runtime_name == "podman"

    daemon_hyperv = HostAgentDaemon(host_id="host-hyperv-01", runtime="hyperv")
    assert daemon_hyperv.collector.runtime_name == "hyperv"

    daemon_linux = HostAgentDaemon(host_id="host-linux-01", runtime="linux")
    assert daemon_linux.collector.runtime_name == "linux"


@pytest.mark.asyncio
async def test_host_agent_daemon_collect_inventory_snapshot_pluggable():
    """Test HostAgentDaemon collects normalized inventory snapshot via active collector."""
    daemon = HostAgentDaemon(host_id="host-podman-01", runtime="podman")
    snapshot = daemon.collect_inventory_snapshot()

    assert snapshot["host_id"] == "host-podman-01"
    assert snapshot["host_info"]["provider_type"] == "podman"
    assert len(snapshot["networks"]) >= 1
    assert snapshot["networks"][0]["driver"] == "bridge"

    # Verify backward-compatible alias
    docker_snapshot = daemon.collect_docker_snapshot()
    assert docker_snapshot == snapshot

