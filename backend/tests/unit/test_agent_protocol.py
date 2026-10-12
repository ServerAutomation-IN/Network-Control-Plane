"""Unit Tests for Remote Host Agent Protocol Schemas — Network Control Plane"""

from datetime import datetime, timezone
from app.schemas.agent import (
    AgentHeartbeatRequest,
    AgentHeartbeatResponse,
    AgentHostInfo,
    AgentNetworkInfo,
    AgentSubnetInfo,
    AgentContainerInfo,
    AgentAttachmentInfo,
    AgentInventorySnapshot,
    AgentEventMessage,
    AgentCommandRequest,
    AgentCommandResult,
    AgentResponseEnvelope,
)


def test_agent_heartbeat_request_validation():
    """Test AgentHeartbeatRequest instantiates with defaults and custom metrics."""
    req = AgentHeartbeatRequest(
        host_id="host-agent-01",
        cpu_utilization_pct=12.5,
        memory_utilization_pct=45.2,
    )
    assert req.host_id == "host-agent-01"
    assert req.status == "HEALTHY"
    assert req.cpu_utilization_pct == 12.5
    assert isinstance(req.timestamp, datetime)


def test_agent_inventory_snapshot_validation():
    """Test AgentInventorySnapshot nested schemas structure."""
    host_info = AgentHostInfo(
        hostname="node-01.local",
        docker_version="24.0.5",
        os="Ubuntu 22.04 LTS",
        architecture="x86_64",
        environment="production",
    )
    net_info = AgentNetworkInfo(
        provider_ref_id="net-12345",
        name="prod_overlay",
        driver="overlay",
        subnets=[AgentSubnetInfo(subnet="10.100.0.0/16", gateway="10.100.0.1")],
    )
    cnt_info = AgentContainerInfo(
        provider_ref_id="cnt-98765",
        name="web_frontend",
        image="nginx:latest",
        status="running",
        attachments=[
            AgentAttachmentInfo(network_name="prod_overlay", ip_address="10.100.0.42")
        ],
    )
    snapshot = AgentInventorySnapshot(
        host_id="host-agent-01",
        host_info=host_info,
        networks=[net_info],
        containers=[cnt_info],
    )

    assert snapshot.host_id == "host-agent-01"
    assert len(snapshot.networks) == 1
    assert snapshot.networks[0].driver == "overlay"
    assert snapshot.containers[0].attachments[0].ip_address == "10.100.0.42"


def test_agent_event_message_validation():
    """Test AgentEventMessage model validation."""
    event = AgentEventMessage(
        host_id="host-agent-01",
        event_type="container.die",
        resource_type="container",
        resource_id="cnt-98765",
        attributes={"exitCode": "137"},
    )
    assert event.event_type == "container.die"
    assert event.attributes["exitCode"] == "137"


def test_agent_command_request_result():
    """Test AgentCommandRequest and AgentCommandResult models."""
    cmd = AgentCommandRequest(
        command_id="cmd-001",
        action="CREATE_NETWORK",
        payload={"name": "test_net", "driver": "bridge"},
    )
    assert cmd.action == "CREATE_NETWORK"

    res = AgentCommandResult(
        command_id="cmd-001",
        success=True,
        result_data={"network_id": "net-999"},
    )
    assert res.success is True
    assert res.result_data["network_id"] == "net-999"


def test_agent_response_envelope():
    """Test AgentResponseEnvelope generic wrapper."""
    envelope = AgentResponseEnvelope[dict](
        status="success",
        message="Heartbeat ACK",
        data={"ack": True},
    )
    assert envelope.status == "success"
    assert envelope.data["ack"] is True
